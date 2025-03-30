#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Finder - 高效的四字母域名查找工具

本工具通过DNS初筛和可选的API验证，帮助用户查找未注册的域名。
具备多线程处理和断点续查功能，适合大批量域名可用性检测。

作者: Alan
许可证: MIT
"""

import itertools
import socket
import pandas as pd
import time
import os
import logging
import argparse
import threading
import json
import requests
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional, Any, Union

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("domain_finder.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== 配置常量 ==========
# 默认易读字符集（排除易混淆字符 i, l, o, q, v, x, z）
DEFAULT_EASY_LETTERS = 'abcdefhkmnprstuwy'
# 数字字符集
DIGITS = '0123456789'
# 所有字母
ALL_LETTERS = string.ascii_lowercase
# 字母和数字组合
ALPHANUMERIC = string.ascii_lowercase + DIGITS

# API速率限制
RATE_LIMIT_PORKBUN = 11  # Porkbun限制每10秒一次查询，留出1秒余量
RATE_LIMIT_DYNADOT = 2   # Dynadot API限制未知，假设2秒

# 默认文件路径
DEFAULT_CHECKED_FILE = 'checked_domains.csv'
DEFAULT_AVAILABLE_FILE = 'available_domains.csv'
DEFAULT_ERROR_LOG = 'errors.log'
DEFAULT_CONFIG_FILE = 'config.json'
DEFAULT_TLD = '.com'  # 默认顶级域名

# ========== 工具类 ==========
class Counter:
    """线程安全的计数器"""
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()
    
    def increment(self):
        with self.lock:
            self.value += 1
            return self.value
    
    def get(self):
        with self.lock:
            return self.value

class APIConfig:
    """API配置类"""
    def __init__(self):
        self.providers = {}  # 存储多个提供商的配置
        self.active_providers = []  # 活跃的API提供商列表
    
    def add_provider(self, provider: str, config: Dict[str, Any]) -> None:
        """添加API提供商配置"""
        self.providers[provider.lower()] = config
        if config.get('active', True):  # 默认为活跃状态
            self.active_providers.append(provider.lower())
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """获取指定提供商的配置"""
        return self.providers.get(provider.lower(), {})
    
    def get_random_active_provider(self) -> str:
        """获取随机活跃提供商"""
        if not self.active_providers:
            return None
        return random.choice(self.active_providers)
    
    def is_provider_active(self, provider: str) -> bool:
        """检查提供商是否活跃"""
        return provider.lower() in self.active_providers
    
    @classmethod
    def from_file(cls, config_file=DEFAULT_CONFIG_FILE):
        """从配置文件加载API配置"""
        config = cls()
        
        if not os.path.exists(config_file):
            logger.warning(f"配置文件 {config_file} 不存在")
            return config
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            # 兼容旧配置格式
            if isinstance(data, dict) and 'provider' in data:
                # 旧格式
                provider = data.get('provider')
                if provider:
                    provider_config = {
                        'api_key': data.get('api_key'),
                        'api_secret': data.get('api_secret'),
                        'active': True
                    }
                    config.add_provider(provider, provider_config)
            
            # 新的多提供商格式
            elif isinstance(data, dict) and 'providers' in data:
                providers = data.get('providers', {})
                for provider_name, provider_config in providers.items():
                    config.add_provider(provider_name, provider_config)
            
            # 检查是否有活跃的提供商
            if not config.active_providers:
                logger.warning("配置文件中没有找到活跃的API提供商")
        
        except Exception as e:
            logger.error(f"加载API配置文件出错: {str(e)}")
        
        return config

# ========== 域名生成器 ==========
def generate_domains(characters: str, length: int = 4, limit: int = 0, 
                    prefix: str = "", suffix: str = "",
                    tld: str = DEFAULT_TLD,
                    exclude_set: Set[str] = None,
                    pattern: str = None) -> List[str]:
    """
    生成指定长度的域名组合
    
    Args:
        characters: 用于生成域名的字符集
        length: 域名长度(不含前缀后缀)
        limit: 生成的域名数量限制
        prefix: 域名前缀
        suffix: 域名后缀
        tld: 顶级域名，如.com
        exclude_set: 已检查过的域名集合
        pattern: 生成模式，如"l"=仅字母,"d"=仅数字,"ld"=字母和数字混合

    Returns:
        生成的域名列表
    """
    if exclude_set is None:
        exclude_set = set()
    
    # 根据模式调整字符集
    if pattern:
        char_set = ""
        if 'l' in pattern.lower():
            char_set += string.ascii_lowercase
        if 'd' in pattern.lower():
            char_set += string.digits
        if char_set:
            characters = char_set
    
    # 计算有效长度
    effective_length = length
    
    if effective_length <= 0:
        logger.error(f"域名长度必须大于0")
        return []
    
    # 计算总组合数
    total_combinations = len(characters) ** effective_length
    actual_limit = limit if limit > 0 else total_combinations
    
    if actual_limit > 10000 and limit > 0:
        logger.warning(f"生成的组合数量非常大 ({actual_limit})，这可能需要一些时间")
    else:
        logger.info(f"将生成约{min(total_combinations, actual_limit)}个组合")
    
    # 生成组合
    generated = []
    count = 0
    
    for combo in itertools.product(characters, repeat=effective_length):
        domain_part = ''.join(combo)
        full_domain = f"{prefix}{domain_part}{suffix}{tld}"
        
        # 检查是否已经处理过
        if full_domain in exclude_set:
            continue
        
        generated.append(full_domain)
        count += 1
        
        # 达到数量限制时停止
        if limit > 0 and count >= limit:
            break
    
    logger.info(f"成功生成{len(generated)}个域名")
    return generated

# ========== DNS检查器 ==========
def dns_check(domain: str) -> Tuple[str, bool, Optional[str]]:
    """
    通过DNS查询检查域名是否已注册
    
    Args:
        domain: 要检查的域名

    Returns:
        (域名, 是否已注册, 错误信息)
    """
    try:
        socket.gethostbyname(domain)
        return domain, True, None  # 域名存在DNS记录，可能已注册
    except socket.gaierror:
        # 无DNS记录，可能未注册
        return domain, False, None
    except Exception as e:
        # 发生错误，记录并假设域名存在（谨慎处理）
        error_msg = f"DNS查询错误: {str(e)}"
        return domain, True, error_msg

# ========== API检查器 ==========
def api_check(domain: str, api_config: APIConfig, provider: str = None) -> Tuple[str, bool, Optional[str]]:
    """
    通过API检查域名是否可注册
    
    Args:
        domain: 要检查的域名
        api_config: API配置
        provider: 指定API提供商，不指定则使用随机活跃提供商

    Returns:
        (域名, 是否可用, 错误/价格信息)
    """
    # 如果没有指定提供商，随机选择一个活跃的提供商
    if not provider:
        provider = api_config.get_random_active_provider()
    
    if not provider:
        return domain, False, "未配置API"
    
    # 获取提供商配置
    provider_config = api_config.get_provider_config(provider)
    if not provider_config:
        return domain, False, f"未找到提供商配置: {provider}"
    
    # 根据提供商调用相应的API
    if provider.lower() == 'porkbun':
        return porkbun_check(domain, provider_config)
    elif provider.lower() == 'dynadot':
        return dynadot_check(domain, provider_config)
    
    # 可以添加更多API提供商支持
    
    return domain, False, f"不支持的API提供商: {provider}"

def porkbun_check(domain: str, config: Dict[str, Any]) -> Tuple[str, bool, Optional[str]]:
    """
    通过Porkbun API检查域名是否可注册
    
    Args:
        domain: 要检查的域名
        config: Porkbun API配置

    Returns:
        (域名, 是否可用, 错误/价格信息)
    """
    api_url = f"https://api.porkbun.com/api/json/v3/domain/checkDomain/{domain}"
    
    payload = {
        "apikey": config.get('api_key'),
        "secretapikey": config.get('api_secret')
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    logger.debug(f"Porkbun API检查域名: {domain}")
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "SUCCESS":
                response_data = data.get("response", {})
                available = response_data.get("avail") == "yes"
                price = response_data.get("price", "未知")
                return domain, available, f"Porkbun价格: {price}"
            else:
                error_msg = data.get("message", "未知错误")
                return domain, False, f"Porkbun API错误: {error_msg}"
        elif response.status_code == 400 and "within 10 seconds used" in response.text:
            # 速率限制错误
            return domain, None, "Porkbun速率限制"
        else:
            return domain, False, f"Porkbun HTTP错误: {response.status_code}"
    except Exception as e:
        return domain, False, f"Porkbun请求异常: {str(e)}"

def dynadot_check(domain: str, config: Dict[str, Any]) -> Tuple[str, bool, Optional[str]]:
    """
    通过Dynadot API检查域名是否可注册
    
    Args:
        domain: 要检查的域名
        config: Dynadot API配置

    Returns:
        (域名, 是否可用, 错误/价格信息)
    """
    api_key = config.get('api_key')
    if not api_key:
        return domain, False, "未提供Dynadot API密钥"
    
    # 使用JSON API格式
    api_url = "https://api.dynadot.com/api3.json"
    
    params = {
        "key": api_key,
        "command": "search",
        "domain0": domain  # 正确的参数名，必须是domain0而不是domain
    }
    
    logger.debug(f"Dynadot API检查域名: {domain}")
    
    try:
        response = requests.get(api_url, params=params, timeout=10)
        
        if response.status_code == 200:
            try:
                data = response.json()
                logger.debug(f"Dynadot API响应: {data}")
                
                # 检查错误
                if "error" in data:
                    error_msg = data.get("error", "未知错误")
                    return domain, False, f"Dynadot API错误: {error_msg}"
                
                # 检查SearchResponse中的错误
                if "SearchResponse" in data and "Error" in data["SearchResponse"]:
                    error_msg = data["SearchResponse"].get("Error", "未知错误")
                    return domain, False, f"Dynadot API错误: {error_msg}"
                
                # 检查搜索结果
                if "SearchResponse" in data and "SearchResults" in data["SearchResponse"]:
                    results = data["SearchResponse"]["SearchResults"]
                    if isinstance(results, list) and len(results) > 0:
                        result = results[0]
                        # 正确处理"yes"/"no"字符串值
                        available_str = result.get("Available", "no")
                        available = (available_str.lower() == "yes")
                        
                        price = result.get("Price", "未知")
                        currency = result.get("Currency", "USD")
                        
                        if available:
                            return domain, True, f"Dynadot价格: {price} {currency}"
                        else:
                            return domain, False, "Dynadot: 域名已注册"
                
                # 无法解析结果
                return domain, False, "Dynadot API返回格式异常"
            except json.JSONDecodeError:
                return domain, False, f"Dynadot JSON解析错误: {response.text[:100]}..."
        else:
            return domain, False, f"Dynadot HTTP错误: {response.status_code}"
    except Exception as e:
        logger.error(f"Dynadot请求异常: {str(e)}")
        return domain, False, f"Dynadot请求异常: {str(e)}"

# ========== 数据管理 ==========
def load_checked_domains(file_path: str) -> Tuple[pd.DataFrame, Set[str]]:
    """
    加载已检查的域名数据
    
    Args:
        file_path: CSV文件路径

    Returns:
        (DataFrame, 已检查域名集合)
    """
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # 确保所有必需的列都存在
            required_columns = ["domain", "dns_checked", "api_verified", "available"]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = False if col != "domain" else ""
            
            # 提取已检查的域名集合
            checked_set = set(df['domain'].tolist())
            logger.info(f"已加载{len(checked_set)}个已检查的域名")
            return df, checked_set
        except Exception as e:
            logger.error(f"加载CSV文件出错: {str(e)}")
            return pd.DataFrame(columns=["domain", "dns_checked", "api_verified", "available", "note"]), set()
    else:
        return pd.DataFrame(columns=["domain", "dns_checked", "api_verified", "available", "note"]), set()

def save_checked_domains(df: pd.DataFrame, file_path: str):
    """保存已检查的域名数据"""
    try:
        df.to_csv(file_path, index=False)
        logger.debug(f"已保存检查结果到 {file_path}")
    except Exception as e:
        logger.error(f"保存CSV文件出错: {str(e)}")

def save_available_domain(domain: str, note: str, file_path: str):
    """保存可用域名到文件"""
    try:
        with open(file_path, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{domain},{timestamp},{note}\n")
    except Exception as e:
        logger.error(f"保存可用域名出错: {str(e)}")

def log_error(domain: str, error: str, file_path: str):
    """记录错误到日志文件"""
    try:
        with open(file_path, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - {domain} - {error}\n")
    except Exception as e:
        logger.error(f"写入错误日志出错: {str(e)}")

# ========== 主程序 ==========
def run_dns_batch(domains: List[str], 
                checked_df: pd.DataFrame,
                available_file: str, 
                error_file: str,
                counter: Counter,
                max_workers: int = 20) -> pd.DataFrame:
    """
    运行DNS批量检查
    
    Args:
        domains: 要检查的域名列表
        checked_df: 已检查域名的DataFrame
        available_file: 可用域名输出文件
        error_file: 错误日志文件
        counter: 计数器
        max_workers: 最大并发线程数

    Returns:
        更新后的DataFrame
    """
    
    new_rows = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_domain = {executor.submit(dns_check, domain): domain for domain in domains}
        
        for future in as_completed(future_to_domain):
            try:
                domain, is_registered, error = future.result()
                count = counter.increment()
                
                # 如果出现错误，记录到错误日志
                if error:
                    log_error(domain, error, error_file)
                    status = "❓"
                else:
                    status = "❌" if is_registered else "✅"
                
                # 显示进度
                logger.info(f"[{count}/{len(domains)}] {status} {domain}")
                
                # 记录结果
                row = {
                    "domain": domain,
                    "dns_checked": True,
                    "api_verified": False,
                    "available": not is_registered,
                    "note": error if error else ("已注册" if is_registered else "DNS无记录，可能可用")
                }
                new_rows.append(row)
                
                # 如果看起来可用，添加到候选可用域名列表
                if not is_registered:
                    save_available_domain(domain, "待API验证", available_file)
            except Exception as e:
                logger.error(f"处理域名时出错: {str(e)}")
    
    # 整合新的结果
    updated_df = pd.concat([checked_df, pd.DataFrame(new_rows)], ignore_index=True)
    return updated_df

def run_api_verification(domains: List[str], 
                       checked_df: pd.DataFrame,
                       available_file: str, 
                       error_file: str,
                       api_config: APIConfig,
                       use_multi_api: bool = False,
                       max_workers: int = 1) -> pd.DataFrame:
    """
    使用API验证域名是否可用
    
    Args:
        domains: 要验证的域名列表
        checked_df: 已检查域名的DataFrame
        available_file: 可用域名输出文件
        error_file: 错误日志文件
        api_config: API配置
        use_multi_api: 是否使用多个API并行查询
        max_workers: API并行查询的最大线程数

    Returns:
        更新后的DataFrame
    """
    
    if not api_config.active_providers:
        logger.error("未提供有效的API配置，无法进行API验证")
        return checked_df
    
    logger.info(f"使用的API提供商: {', '.join(api_config.active_providers)}")
    
    # 单API顺序验证
    if not use_multi_api or max_workers <= 1:
        return run_sequential_api_verification(domains, checked_df, available_file, error_file, api_config)
    
    # 多API并行验证
    return run_parallel_api_verification(domains, checked_df, available_file, error_file, api_config, max_workers)

def run_sequential_api_verification(domains: List[str], 
                                  checked_df: pd.DataFrame,
                                  available_file: str, 
                                  error_file: str,
                                  api_config: APIConfig) -> pd.DataFrame:
    """单API顺序验证域名"""
    
    for i, domain in enumerate(domains):
        try:
            logger.info(f"[{i+1}/{len(domains)}] API验证域名: {domain}")
            
            # 随机选择一个API提供商
            provider = api_config.get_random_active_provider()
            provider_config = api_config.get_provider_config(provider)
            
            # 获取提供商的速率限制
            rate_limit = RATE_LIMIT_PORKBUN
            if provider.lower() == 'dynadot':
                rate_limit = RATE_LIMIT_DYNADOT
            
            # 执行API检查
            domain, is_available, note = api_check(domain, api_config, provider)
            
            # 处理速率限制
            if is_available is None and "速率限制" in note:
                logger.warning(f"达到{provider}速率限制，等待{rate_limit}秒...")
                time.sleep(rate_limit)
                # 重试，可能使用不同的API
                domain, is_available, note = api_check(domain, api_config)
            
            # 更新数据框中的结果
            mask = checked_df['domain'] == domain
            checked_df.loc[mask, 'api_verified'] = True
            
            if is_available:
                checked_df.loc[mask, 'available'] = True
                checked_df.loc[mask, 'note'] = note
                logger.info(f"✅ 确认可用: {domain} ({note})")
                save_available_domain(domain, f"API已确认 - {note}", available_file)
            else:
                checked_df.loc[mask, 'available'] = False
                checked_df.loc[mask, 'note'] = note
                logger.info(f"❌ 已注册: {domain} ({note})")
            
            # 添加延迟以遵守API速率限制
            logger.debug(f"等待{rate_limit}秒以遵守速率限制...")
            time.sleep(rate_limit)
            
        except Exception as e:
            error_msg = f"API验证出错: {str(e)}"
            logger.error(error_msg)
            log_error(domain, error_msg, error_file)
    
    return checked_df

def run_parallel_api_verification(domains: List[str], 
                                checked_df: pd.DataFrame,
                                available_file: str, 
                                error_file: str,
                                api_config: APIConfig,
                                max_workers: int = 3) -> pd.DataFrame:
    """多API并行验证域名"""
    
    # 为每个域名分配一个API提供商
    domain_to_provider = {}
    
    # 将域名均匀分配给不同的API提供商
    providers = api_config.active_providers
    if not providers:
        logger.error("没有活跃的API提供商配置")
        return checked_df
    
    for i, domain in enumerate(domains):
        provider = providers[i % len(providers)]
        domain_to_provider[domain] = provider
    
    # 按提供商分组
    provider_to_domains = {}
    for domain, provider in domain_to_provider.items():
        if provider not in provider_to_domains:
            provider_to_domains[provider] = []
        provider_to_domains[provider].append(domain)
    
    # 创建每个提供商的API检查任务
    tasks = []
    for provider, provider_domains in provider_to_domains.items():
        tasks.append((provider, provider_domains))
    
    logger.info(f"创建{len(tasks)}个API验证任务，使用{min(max_workers, len(tasks))}个线程并行处理")
    
    # 使用线程池并行执行API检查任务
    results = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(tasks))) as executor:
        futures = []
        
        for provider, provider_domains in tasks:
            future = executor.submit(
                process_api_batch, provider_domains, provider, 
                api_config, available_file, error_file
            )
            futures.append(future)
        
        for future in as_completed(futures):
            try:
                batch_results = future.result()
                results.extend(batch_results)
            except Exception as e:
                logger.error(f"API批处理出错: {str(e)}")
    
    # 更新DataFrame
    for domain, is_available, note in results:
        mask = checked_df['domain'] == domain
        if mask.any():
            checked_df.loc[mask, 'api_verified'] = True
            checked_df.loc[mask, 'available'] = is_available
            checked_df.loc[mask, 'note'] = note
    
    return checked_df

def process_api_batch(domains: List[str], 
                    provider: str, 
                    api_config: APIConfig,
                    available_file: str,
                    error_file: str) -> List[Tuple[str, bool, str]]:
    """处理一批域名的API验证"""
    
    results = []
    provider_config = api_config.get_provider_config(provider)
    
    # 获取提供商的速率限制
    rate_limit = RATE_LIMIT_PORKBUN
    if provider.lower() == 'dynadot':
        rate_limit = RATE_LIMIT_DYNADOT
    
    for i, domain in enumerate(domains):
        try:
            logger.info(f"[{provider}] [{i+1}/{len(domains)}] 验证域名: {domain}")
            
            # 执行API检查
            domain, is_available, note = api_check(domain, api_config, provider)
            
            # 记录结果
            results.append((domain, is_available, note))
            
            # 处理可用域名
            if is_available:
                logger.info(f"✅ 确认可用: {domain} ({note})")
                save_available_domain(domain, f"API已确认 - {note}", available_file)
            else:
                logger.info(f"❌ 已注册: {domain} ({note})")
            
            # 添加延迟以遵守API速率限制
            logger.debug(f"[{provider}] 等待{rate_limit}秒...")
            time.sleep(rate_limit)
            
        except Exception as e:
            error_msg = f"API验证出错: {str(e)}"
            logger.error(error_msg)
            log_error(domain, error_msg, error_file)
            results.append((domain, False, error_msg))
    
    return results

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(description='域名查找工具')
    
    # 基本参数
    parser.add_argument('--characters', default=DEFAULT_EASY_LETTERS, 
                      help=f'使用的字符集 (默认: {DEFAULT_EASY_LETTERS})')
    parser.add_argument('--length', type=int, default=4, 
                      help='域名长度 (默认: 4)')
    parser.add_argument('--limit', type=int, default=1000, 
                      help='每次检查的域名数量限制 (默认: 1000)')
    parser.add_argument('--prefix', default='', 
                      help='域名前缀')
    parser.add_argument('--suffix', default='', 
                      help='域名后缀')
    parser.add_argument('--tld', default=DEFAULT_TLD, 
                      help=f'顶级域名 (默认: {DEFAULT_TLD})')
    
    # 字符类型参数
    parser.add_argument('--pattern', choices=['l', 'd', 'ld', 'dl'], default=None,
                      help='域名模式: l=仅字母, d=仅数字, ld/dl=字母数字混合')
    parser.add_argument('--letters', action='store_true',
                      help='使用所有字母作为字符集')
    parser.add_argument('--digits', action='store_true',
                      help='使用数字作为字符集')
    parser.add_argument('--alphanumeric', action='store_true',
                      help='使用字母和数字作为字符集')
    
    # 性能参数
    parser.add_argument('--threads', type=int, default=20, 
                      help='DNS检查的并发线程数 (默认: 20)')
    parser.add_argument('--api-workers', type=int, default=1,
                      help='API验证的并发线程数 (默认: 1，设置大于1启用多API并行)')
    
    # 文件路径参数
    parser.add_argument('--check-file', default=DEFAULT_CHECKED_FILE, 
                      help='已检查域名文件路径')
    parser.add_argument('--available-file', default=DEFAULT_AVAILABLE_FILE, 
                      help='可用域名文件路径')
    parser.add_argument('--error-file', default=DEFAULT_ERROR_LOG, 
                      help='错误日志文件')
    parser.add_argument('--config-file', default=DEFAULT_CONFIG_FILE, 
                      help='API配置文件')
    
    # 功能开关
    parser.add_argument('--verify-api', action='store_true', 
                      help='是否使用API验证DNS可用的域名')
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='显示详细日志')
    parser.add_argument('--only-verify-api', action='store_true',
                      help='仅执行API验证步骤，跳过DNS检查')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 输出程序开始信息
    logger.info("="*50)
    logger.info("域名查找工具启动")
    logger.info(f"参数: {vars(args)}")
    
    # 确定字符集
    characters = args.characters
    if args.letters:
        characters = ALL_LETTERS
    elif args.digits:
        characters = DIGITS
    elif args.alphanumeric:
        characters = ALPHANUMERIC
    
    # 加载已检查的域名
    checked_df, checked_set = load_checked_domains(args.check_file)
    
    # 仅执行API验证步骤
    if args.only_verify_api:
        return run_only_api_verification(args, checked_df)
    
    # 生成待检查的域名
    domains = generate_domains(
        characters=characters,
        length=args.length,
        limit=args.limit,
        prefix=args.prefix,
        suffix=args.suffix,
        tld=args.tld,
        exclude_set=checked_set,
        pattern=args.pattern
    )
    
    if not domains:
        logger.warning("没有新的域名需要检查")
        return
    
    # 创建计数器
    counter = Counter()
    
    # 第一阶段：DNS快速初筛
    logger.info("="*30)
    logger.info(f"开始DNS批量检查，共{len(domains)}个域名")
    updated_df = run_dns_batch(
        domains=domains,
        checked_df=checked_df,
        available_file=args.available_file,
        error_file=args.error_file,
        counter=counter,
        max_workers=args.threads
    )
    
    # 保存检查结果
    save_checked_domains(updated_df, args.check_file)
    logger.info(f"DNS检查完成，结果已保存到 {args.check_file}")
    
    # 第二阶段：API精确验证（如果需要）
    if args.verify_api:
        run_api_verification_stage(args, updated_df)
    
    # 显示统计信息
    show_statistics(updated_df, len(domains), args.verify_api)

def run_only_api_verification(args, checked_df):
    """仅运行API验证步骤"""
    logger.info("="*30)
    logger.info("仅执行API验证步骤，跳过DNS检查")
    
    # 筛选出DNS检查后可能可用但未经API验证的域名
    possibly_available = checked_df[
        (checked_df['dns_checked'] == True) & 
        (checked_df['api_verified'] == False) & 
        (checked_df['available'] == True)
    ]['domain'].tolist()
    
    if not possibly_available:
        logger.warning("没有找到需要API验证的域名")
        return
    
    logger.info(f"找到{len(possibly_available)}个待验证域名")
    
    # 运行API验证阶段
    run_api_verification_stage(args, checked_df, possibly_available)
    
    # 显示统计信息
    show_statistics(checked_df, len(possibly_available), True)

def run_api_verification_stage(args, checked_df, domains=None):
    """运行API验证阶段"""
    logger.info("="*30)
    logger.info("开始API精确验证...")
    
    # 加载API配置
    api_config = APIConfig.from_file(args.config_file)
    
    if not api_config.active_providers:
        logger.error(f"无法从{args.config_file}加载有效的API配置，请检查配置文件")
        logger.info("API验证已跳过")
        return checked_df
    
    logger.info(f"已加载API配置 (提供商: {', '.join(api_config.active_providers)})")
    
    # 如果没有指定域名，则从DataFrame中筛选
    if domains is None:
        domains = checked_df[
            (checked_df['dns_checked'] == True) & 
            (checked_df['api_verified'] == False) & 
            (checked_df['available'] == True)
        ]['domain'].tolist()
    
    logger.info(f"需要API验证的域名数量: {len(domains)}")
    
    if not domains:
        logger.info("没有域名需要API验证")
        return checked_df
    
    # 运行API验证
    use_multi_api = args.api_workers > 1 and len(api_config.active_providers) > 1
    if use_multi_api:
        logger.info(f"启用多API并行验证，使用{args.api_workers}个线程")
    
    final_df = run_api_verification(
        domains=domains,
        checked_df=checked_df,
        available_file=args.available_file,
        error_file=args.error_file,
        api_config=api_config,
        use_multi_api=use_multi_api,
        max_workers=args.api_workers
    )
    
    # 保存最终结果
    save_checked_domains(final_df, args.check_file)
    logger.info(f"API验证完成，结果已保存到 {args.check_file}")
    
    return final_df

def show_statistics(df, total_checked, verified_api=False):
    """显示统计信息"""
    available_count = len(df[df['available'] == True])
    verified_count = len(df[
        (df['api_verified'] == True) & 
        (df['available'] == True)
    ])
    
    logger.info("="*30)
    logger.info("检查完成！统计信息:")
    logger.info(f"总检查域名数: {total_checked}")
    logger.info(f"DNS检查可能可用: {available_count}")
    
    if verified_api:
        logger.info(f"API确认可用: {verified_count}")
    
    logger.info(f"所有可用域名已保存到: {DEFAULT_AVAILABLE_FILE}")
    logger.info("="*50)

# 导出关键组件以便导入
__all__ = [
    'generate_domains',
    'dns_check',
    'api_check',
    'porkbun_check',
    'dynadot_check',
    'load_checked_domains',
    'save_checked_domains',
    'save_available_domain',
    'log_error',
    'APIConfig',
    'Counter'
]

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n用户中断检查，已保存当前进度")
    except Exception as e:
        logger.error(f"程序执行错误: {str(e)}", exc_info=True) 