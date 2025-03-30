#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名查找器 - 自动批量检查版本
此脚本自动执行多组域名检查，并将结果保存到CSV文件中
无需用户干预，适合后台运行
"""

import os
import sys
import platform
import subprocess
import time
import datetime
import csv
import argparse
import itertools
import string

# 设置环境变量跳过系统版本检查
os.environ['SYSTEM_VERSION_COMPAT'] = '1'

def log(message):
    """记录日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_domain_checker(args, timeout=None):
    """运行域名检查器"""
    cmd = [sys.executable, 'domain_finder.py'] + args
    log(f"执行命令: {' '.join(cmd)}")
    
    try:
        # 使用超时参数，避免某些检查卡住
        process = subprocess.run(cmd, timeout=timeout, check=False)
        
        if process.returncode != 0:
            log(f"域名检查器异常退出，返回码: {process.returncode}")
            return False
        else:
            log("域名检查器已完成运行")
            return True
            
    except subprocess.TimeoutExpired:
        log(f"命令执行超时（{timeout}秒），强制终止")
        return False
    except KeyboardInterrupt:
        log("用户中断操作...")
        return False
    except Exception as e:
        log(f"执行域名检查器时出错: {str(e)}")
        return False

def get_domain_counts():
    """获取当前已检查和可用域名数量"""
    checked_count = 0
    available_count = 0
    
    try:
        if os.path.exists('checked_domains.csv'):
            with open('checked_domains.csv', 'r') as f:
                checked_count = sum(1 for _ in f)
    except:
        pass
        
    try:
        if os.path.exists('available_domains.csv'):
            with open('available_domains.csv', 'r') as f:
                available_count = sum(1 for _ in f)
    except:
        pass
        
    return checked_count, available_count

def save_batch_progress(batch_info):
    """保存批次进度到CSV文件"""
    fieldnames = ['timestamp', 'batch_type', 'length', 'limit', 'success', 
                  'checked_count', 'available_count', 'duration']
    
    file_exists = os.path.exists('batch_progress.csv')
    
    with open('batch_progress.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow(batch_info)

def run_auto_batch():
    """运行自动批量检查"""
    log("开始自动批量检查流程...")
    
    start_time = time.time()
    
    # 1. 获取初始域名数量
    initial_checked, initial_available = get_domain_counts()
    log(f"初始状态：已检查域名 {initial_checked}，可用域名 {initial_available}")
    
    # 2. 依次进行多种检查
    # 先检查3字母和4字母域名
    lengths = [3, 4, 5]
    batches = [100, 200, 500]
    
    for length in lengths:
        for batch in batches:
            batch_start = time.time()
            
            log(f"--------------------------------------------------")
            log(f"正在检查长度为{length}的域名，批次大小: {batch}")
            
            success = run_domain_checker([
                '--letters', 
                '--length', str(length), 
                '--limit', str(batch), 
                '--threads', '50'
            ], timeout=600)  # 10分钟超时
            
            # 记录批次信息
            checked, available = get_domain_counts()
            duration = time.time() - batch_start
            
            batch_info = {
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'batch_type': 'basic',
                'length': length,
                'limit': batch,
                'success': success,
                'checked_count': checked,
                'available_count': available,
                'duration': round(duration, 2)
            }
            
            save_batch_progress(batch_info)
            
            log(f"批次完成: 已检查 {checked} 个域名，发现 {available} 个可用域名")
            log(f"耗时: {round(duration, 2)}秒")
            
            if not success:
                log("该批次检查失败，将继续下一个批次")
            
            # 每次检查后暂停几秒，避免请求过于频繁
            log("暂停10秒...")
            time.sleep(10)
    
    # 3. 进行API验证检查
    log("--------------------------------------------------")
    log("所有基本检查完成，开始API验证...")
    
    batch_start = time.time()
    api_success = run_domain_checker(['--only-verify-api', '--api-workers', '1'], timeout=3600)  # 1小时超时
    
    # 记录API验证批次信息
    checked, available = get_domain_counts()
    duration = time.time() - batch_start
    
    batch_info = {
        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'batch_type': 'api_verify',
        'length': 'all',
        'limit': 'all',
        'success': api_success,
        'checked_count': checked,
        'available_count': available,
        'duration': round(duration, 2)
    }
    
    save_batch_progress(batch_info)
    
    # 4. 汇总结果
    final_checked, final_available = get_domain_counts()
    total_duration = time.time() - start_time
    
    log("--------------------------------------------------")
    log("批量检查完成！")
    log(f"总耗时: {round(total_duration/60, 2)}分钟")
    log(f"总检查域名: {final_checked} (新增 {final_checked - initial_checked})")
    log(f"总可用域名: {final_available} (新增 {final_available - initial_available})")
    log("--------------------------------------------------")
    
    # 5. 显示可用域名列表（如果数量不太多的话）
    if os.path.exists('available_domains.csv'):
        try:
            with open('available_domains.csv', 'r') as f:
                domains = f.readlines()
                
            if len(domains) < 100:  # 只有当数量不多时才全部显示
                log("可用域名列表:")
                for domain in domains:
                    log(f"  {domain.strip()}")
            else:
                log(f"可用域名过多 ({len(domains)}个)，请直接查看available_domains.csv文件")
        except Exception as e:
            log(f"读取域名文件时出错: {str(e)}")
    
    return True

def run_custom_patterns(patterns, limit_per_pattern=50):
    """运行自定义模式检查"""
    log("开始自定义模式检查...")
    
    start_time = time.time()
    initial_checked, initial_available = get_domain_counts()
    
    total_patterns = len(patterns)
    
    for i, pattern in enumerate(patterns, 1):
        batch_start = time.time()
        
        log(f"--------------------------------------------------")
        log(f"正在检查模式 [{i}/{total_patterns}]: {pattern}")
        
        # 使用pattern参数执行检查
        success = run_domain_checker([
            '--pattern', pattern,
            '--limit', str(limit_per_pattern),
            '--threads', '50'
        ], timeout=300)  # 5分钟超时
        
        # 记录批次信息
        checked, available = get_domain_counts()
        duration = time.time() - batch_start
        
        batch_info = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'batch_type': 'pattern',
            'length': len(pattern),
            'limit': limit_per_pattern,
            'success': success,
            'checked_count': checked,
            'available_count': available,
            'duration': round(duration, 2)
        }
        
        save_batch_progress(batch_info)
        
        log(f"模式完成: 已检查 {checked} 个域名，发现 {available} 个可用域名")
        log(f"耗时: {round(duration, 2)}秒")
        
        # 每次检查后暂停，避免过快请求
        log("暂停5秒...")
        time.sleep(5)
    
    # 可能需要进行API验证
    log("--------------------------------------------------")
    log("所有模式检查完成，开始API验证...")
    
    batch_start = time.time()
    api_success = run_domain_checker(['--only-verify-api', '--api-workers', '1'], timeout=1800)  # 30分钟超时
    
    # 汇总结果
    final_checked, final_available = get_domain_counts()
    total_duration = time.time() - start_time
    
    log("--------------------------------------------------")
    log("自定义模式检查完成！")
    log(f"总耗时: {round(total_duration/60, 2)}分钟")
    log(f"总检查域名: {final_checked} (新增 {final_checked - initial_checked})")
    log(f"总可用域名: {final_available} (新增 {final_available - initial_available})")
    log("--------------------------------------------------")
    
    return True

def run_letter_combinations(length=4, batch_size=100, verify_api=True, include_digits=False):
    """运行字母组合检查"""
    log(f"开始检查长度为{length}的所有字母组合...")
    
    start_time = time.time()
    initial_checked, initial_available = get_domain_counts()
    
    # 确定字符集
    if include_digits:
        chars = string.ascii_lowercase + string.digits
        log(f"使用字符集: 字母+数字 (共{len(chars)}个字符)")
    else:
        chars = string.ascii_lowercase
        log(f"使用字符集: 仅字母 (共{len(chars)}个字符)")
    
    # 常用字母
    common_letters = 'abcdefhkmnprstuwy'
    log(f"使用常用字母集: {common_letters}")
    
    # 计算可能的组合总数
    total_combinations = len(common_letters) ** length
    log(f"理论组合总数: {total_combinations}，将分批处理")
    
    # 创建多个批次，每批次处理一定数量
    batch_count = 10  # 分成10个批次
    batch_size_actual = batch_size  # 每批次处理的域名数量
    
    for batch_idx in range(batch_count):
        batch_start = time.time()
        
        log(f"--------------------------------------------------")
        log(f"正在处理批次 [{batch_idx+1}/{batch_count}]")
        
        # 构建命令参数 - 使用标准的字母参数
        cmd_args = [
            '--letters',  # 使用字母
            '--length', str(length),
            '--limit', str(batch_size_actual),
            '--threads', '50',
            '--characters', common_letters  # 指定使用的字符集
        ]
        
        # 如果需要，添加API验证
        if verify_api:
            cmd_args.append('--verify-api')
            
        # 执行检查
        success = run_domain_checker(cmd_args, timeout=600)  # 10分钟超时
        
        # 记录批次信息
        checked, available = get_domain_counts()
        duration = time.time() - batch_start
        
        batch_info = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'batch_type': 'combination',
            'length': length,
            'limit': batch_size_actual,
            'success': success,
            'checked_count': checked,
            'available_count': available,
            'duration': round(duration, 2)
        }
        
        save_batch_progress(batch_info)
        
        log(f"批次完成: 已检查 {checked} 个域名，发现 {available} 个可用域名")
        log(f"耗时: {round(duration, 2)}秒")
        
        # 每次检查后暂停，防止过快请求
        log("暂停10秒...")
        time.sleep(10)
    
    # 最终汇总
    final_checked, final_available = get_domain_counts()
    total_duration = time.time() - start_time
    
    log("--------------------------------------------------")
    log("字母组合检查完成！")
    log(f"总耗时: {round(total_duration/60, 2)}分钟")
    log(f"总检查域名: {final_checked} (新增 {final_checked - initial_checked})")
    log(f"总可用域名: {final_available} (新增 {final_available - initial_available})")
    log("--------------------------------------------------")
    
    return True

def run_dictionary_check(dict_file, batch_size=50, verify_api=True):
    """使用字典文件进行检查"""
    if not os.path.exists(dict_file):
        log(f"错误: 字典文件 {dict_file} 不存在")
        return False
    
    log(f"开始使用字典文件 {dict_file} 进行检查...")
    
    start_time = time.time()
    initial_checked, initial_available = get_domain_counts()
    
    # 读取字典文件
    try:
        with open(dict_file, 'r') as f:
            words = [line.strip() for line in f if line.strip()]
        
        total_words = len(words)
        log(f"从字典中加载了 {total_words} 个单词")
        
        # 按批次处理
        batch_count = (total_words + batch_size - 1) // batch_size
        
        for i in range(batch_count):
            batch_start = time.time()
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, total_words)
            
            # 创建临时批次文件
            batch_file = f"temp_batch_{i}.txt"
            with open(batch_file, 'w') as f:
                for word in words[start_idx:end_idx]:
                    f.write(word + "\n")
            
            log(f"--------------------------------------------------")
            log(f"正在检查批次 [{i+1}/{batch_count}]: 单词 {start_idx+1}-{end_idx}")
            
            # 构建命令参数
            cmd_args = ['--wordlist', batch_file, '--threads', '50']
            
            # 如果需要，添加API验证
            if verify_api:
                cmd_args.append('--verify-api')
                
            # 执行检查
            success = run_domain_checker(cmd_args, timeout=600)  # 10分钟超时
            
            # 删除临时文件
            try:
                os.remove(batch_file)
            except:
                pass
            
            # 记录批次信息
            checked, available = get_domain_counts()
            duration = time.time() - batch_start
            
            batch_info = {
                'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'batch_type': 'dictionary',
                'length': 'varied',
                'limit': end_idx - start_idx,
                'success': success,
                'checked_count': checked,
                'available_count': available,
                'duration': round(duration, 2)
            }
            
            save_batch_progress(batch_info)
            
            log(f"批次完成: 已检查 {checked} 个域名，发现 {available} 个可用域名")
            log(f"耗时: {round(duration, 2)}秒")
            
            # 每次检查后暂停
            log("暂停10秒...")
            time.sleep(10)
    
    except Exception as e:
        log(f"字典检查过程中出错: {str(e)}")
        return False
    
    # 最终汇总
    final_checked, final_available = get_domain_counts()
    total_duration = time.time() - start_time
    
    log("--------------------------------------------------")
    log("字典检查完成！")
    log(f"总耗时: {round(total_duration/60, 2)}分钟")
    log(f"总检查域名: {final_checked} (新增 {final_checked - initial_checked})")
    log(f"总可用域名: {final_available} (新增 {final_available - initial_available})")
    log("--------------------------------------------------")
    
    return True

def check_environment():
    """检查运行环境"""
    log(f"系统: {platform.system()} {platform.release()}")
    log(f"Python版本: {platform.python_version()}")
    log(f"处理器架构: {platform.machine()}")
    
    # 检查必要文件
    if not os.path.exists('domain_finder.py'):
        log("错误: 无法找到核心文件 domain_finder.py")
        return False
    
    return True

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='域名查找工具 - 自动批量检查版')
    
    # 检查模式
    mode_group = parser.add_argument_group('检查模式')
    mode_group.add_argument('--auto', action='store_true', help='自动执行默认批量检查流程')
    mode_group.add_argument('--letters', action='store_true', help='只检查字母组合')
    mode_group.add_argument('--dict', metavar='FILE', help='使用指定字典文件检查')
    mode_group.add_argument('--pattern', metavar='PATTERN', help='检查指定模式')
    
    # 通用参数
    parser.add_argument('--length', type=int, default=4, help='域名长度，默认为4')
    parser.add_argument('--batch-size', type=int, default=100, help='每批次检查的域名数量，默认为100')
    parser.add_argument('--verify-api', action='store_true', help='执行API验证')
    parser.add_argument('--include-digits', action='store_true', help='在字母组合中包含数字')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    print("=" * 80)
    print("  域名查找工具 - 自动批量检查版")
    print("=" * 80)
    print("此脚本将自动执行多组域名检查，无需用户干预")
    print("您可以按Ctrl+C随时终止检查")
    print("=" * 80)
    
    if not check_environment():
        log("环境检查未通过，程序无法运行")
        return 1
    
    # 根据命令行参数选择执行模式
    try:
        if args.dict:
            log(f"使用字典模式检查，字典文件: {args.dict}")
            run_dictionary_check(args.dict, args.batch_size, args.verify_api)
        elif args.pattern:
            log(f"使用指定模式检查，模式: {args.pattern}")
            run_custom_patterns([args.pattern], args.batch_size)
        elif args.letters:
            log(f"使用字母组合模式检查，长度: {args.length}")
            run_letter_combinations(args.length, args.batch_size, args.verify_api, args.include_digits)
        else:
            # 默认执行完整批量检查
            log("启动默认的批量检查流程...")
            run_auto_batch()
    except KeyboardInterrupt:
        log("用户中断了批量检查")
    except Exception as e:
        log(f"批量检查过程中出错: {str(e)}")
        return 1
    
    log("程序执行完毕")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 