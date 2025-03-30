#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Porkbun API 模块 - 提供域名可用性查询功能

此模块可以独立使用，也可以集成到域名查找工具中。
"""

import requests
import logging
import json
import time
from typing import Dict, Any, Tuple, Optional, List, Union

# 设置日志
logger = logging.getLogger(__name__)

# API常量
API_BASE_URL = "https://api.porkbun.com/api/json/v3/domain/checkDomain"
DEFAULT_TIMEOUT = 10  # 秒
RATE_LIMIT = 11  # 秒 (Porkbun限制每10秒一次查询，留出1秒余量)

class PorkbunAPI:
    """Porkbun API客户端类"""
    
    def __init__(self, api_key: str, api_secret: str = None, timeout: int = DEFAULT_TIMEOUT):
        """
        初始化Porkbun API客户端
        
        Args:
            api_key: Porkbun API密钥
            api_secret: Porkbun API密钥(可选，新版API不一定需要)
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.last_request_time = 0  # 上次请求时间戳
    
    def _respect_rate_limit(self):
        """遵守API速率限制"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < RATE_LIMIT:
            sleep_time = RATE_LIMIT - elapsed
            logger.debug(f"等待 {sleep_time:.2f} 秒以遵守速率限制...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def check_domain(self, domain: str) -> Tuple[bool, Optional[str]]:
        """
        检查域名是否可注册
        
        Args:
            domain: 要检查的域名（完整域名，包含TLD）
            
        Returns:
            Tuple[bool, Optional[str]]: (是否可用, 错误/价格信息)
        """
        # 确保域名是完整的
        if "." not in domain:
            domain += ".com"
            logger.debug(f"补全域名: {domain}")
        
        # 遵守速率限制
        self._respect_rate_limit()
        
        # 构建API URL和数据
        api_url = f"{API_BASE_URL}/{domain}"
        
        payload = {
            "apikey": self.api_key
        }
        
        # 如果有API Secret，添加到请求中
        if self.api_secret:
            payload["secretapikey"] = self.api_secret
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            logger.debug(f"检查域名: {domain}")
            response = requests.post(api_url, json=payload, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # 检查状态
                    if data.get("status") == "SUCCESS":
                        response_data = data.get("response", {})
                        available = response_data.get("avail") == "yes"
                        price = response_data.get("price", "未知")
                        
                        if available:
                            return True, f"价格: {price}"
                        else:
                            return False, "域名已注册"
                    else:
                        error_msg = data.get("message", "未知错误")
                        return False, f"API错误: {error_msg}"
                
                except json.JSONDecodeError:
                    return False, f"JSON解析错误: {response.text[:100]}..."
            
            # 速率限制错误
            elif response.status_code == 400 and "within 10 seconds used" in response.text:
                return None, "Porkbun速率限制"
            else:
                return False, f"HTTP错误 {response.status_code}: {response.text[:100]}..."
        
        except requests.Timeout:
            return False, "请求超时"
        except requests.RequestException as e:
            return False, f"请求异常: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"
    
    def batch_check(self, domains: List[str], max_errors: int = 5) -> Dict[str, Tuple[bool, str]]:
        """
        批量检查多个域名
        
        Args:
            domains: 要检查的域名列表
            max_errors: 最大连续错误次数，超过此值将中止批量查询
            
        Returns:
            Dict[str, Tuple[bool, str]]: {域名: (是否可用, 错误/价格信息)}
        """
        results = {}
        consecutive_errors = 0
        
        for domain in domains:
            available, note = self.check_domain(domain)
            
            # 处理速率限制
            if available is None and "速率限制" in note:
                logger.warning(f"达到Porkbun速率限制，等待{RATE_LIMIT}秒...")
                time.sleep(RATE_LIMIT)
                # 重试
                available, note = self.check_domain(domain)
            
            results[domain] = (available, note)
            
            # 重置或增加连续错误计数
            if "错误" in note or "异常" in note:
                consecutive_errors += 1
                logger.warning(f"连续错误 {consecutive_errors}/{max_errors}: {domain} - {note}")
                
                if consecutive_errors >= max_errors:
                    logger.error(f"连续错误次数超过{max_errors}次，中止批量查询")
                    break
            else:
                consecutive_errors = 0
        
        return results

# 从配置文件加载API
def load_from_config(config_file: str = 'config.json') -> Optional[PorkbunAPI]:
    """
    从配置文件加载Porkbun API客户端
    
    Args:
        config_file: 配置文件路径
    
    Returns:
        PorkbunAPI | None: API客户端实例或None
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        porkbun_config = config.get('providers', {}).get('porkbun', {})
        api_key = porkbun_config.get('api_key')
        api_secret = porkbun_config.get('api_secret')
        
        if not api_key:
            logger.error("配置中未找到Porkbun API密钥")
            return None
        
        active = porkbun_config.get('active', False)
        if not active:
            logger.warning("Porkbun API在配置中被禁用")
        
        return PorkbunAPI(api_key, api_secret)
    
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
        return None

# 简易使用示例
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # 从配置加载API
    api = load_from_config()
    if not api:
        logger.error("无法加载API，请检查配置文件")
        exit(1)
    
    # 测试域名
    test_domains = ["example.com", "google.com", "thisislikelynotregistered12345.com"]
    
    # 单个检查
    for domain in test_domains:
        available, note = api.check_domain(domain)
        status = "✅ 可用" if available else "❌ 不可用"
        logger.info(f"{domain}: {status} - {note}")
        # 添加延迟以遵守Porkbun速率限制
        time.sleep(11)
    
    # 批量检查示例
    # results = api.batch_check(test_domains)
    # for domain, (available, note) in results.items():
    #     status = "✅ 可用" if available else "❌ 不可用"
    #     logger.info(f"{domain}: {status} - {note}") 