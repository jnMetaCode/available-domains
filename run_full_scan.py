#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四字母域名全面扫描工具
专门用于查询所有可能的4字母.com域名
"""

import os
import sys
import platform
import subprocess
import time
import datetime
import csv
import itertools
import signal
import atexit
import string
import argparse

# 设置环境变量跳过系统版本检查
os.environ['SYSTEM_VERSION_COMPAT'] = '1'

def log(message):
    """记录日志"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    # 同时写入日志文件
    with open('full_scan.log', 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")

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
    fieldnames = ['timestamp', 'prefix', 'success', 
                  'checked_count', 'available_count', 'duration']
    
    file_exists = os.path.exists('full_scan_progress.csv')
    
    with open('full_scan_progress.csv', 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow(batch_info)

def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """打印进度条"""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

def generate_prefixes():
    """生成所有可能的1-3字母前缀，确保全面覆盖所有4字母域名"""
    prefixes = []
    
    # 按字母频率排序（常用字母优先）
    common_first = 'etaoinsrhdlucmfywgpbvkjxqz'
    
    # 方法1: 单字母前缀（覆盖所有a???、b???等模式）
    for c in common_first:
        prefixes.append(c)
    
    # 方法2: 对特定常用字母生成两字母前缀，增加命中率
    common_second = common_first[:10]  # 取最常见的10个字母
    for c1 in common_second:
        for c2 in common_second:
            prefixes.append(c1 + c2)
    
    # 方法3: 对排名靠后的字母生成两字母组合，确保完整性
    uncommon = common_first[10:]
    for c in uncommon:
        prefixes.append('a' + c)  # 添加以'a'开头的组合
        prefixes.append('e' + c)  # 添加以'e'开头的组合
        prefixes.append('i' + c)  # 添加以'i'开头的组合
        prefixes.append('t' + c)  # 添加以't'开头的组合
    
    # 方法4: 添加一些特定的三字母前缀，用于更细化扫描
    # 常见三字母前缀，如app, dev, etc
    common_three_letter_prefixes = [
        'app', 'dev', 'web', 'api', 'get', 'buy', 'top', 'pro', 'win', 'new',
        'one', 'our', 'you', 'the', 'all', 'use', 'try', 'pay', 'vip', 'max',
        'hot', 'now', 'job', 'net', 'ipi', 'car', 'eco', 'map', 'air', 'led',
        'pen', 'key', 'fly', 'box', 'fun', 'fit', 'lab', 'gym', 'pet', 'red',
        'tax', 'bet', 'bio', 'diy', 'art', 'toy', 'aid', 'run', 'zen', 'vr'
    ]
    prefixes.extend(common_three_letter_prefixes)
    
    # 根据实际频率调整前缀顺序，越可能有价值的前缀越靠前
    high_priority = []
    for prefix in ['a', 'e', 'i', 'o', 'u']:  # 元音字母优先
        if prefix in prefixes:
            high_priority.append(prefix)
            prefixes.remove(prefix)
    
    # 合并并去重
    prefixes = high_priority + prefixes
    return list(dict.fromkeys(prefixes))  # 去重

def run_full_scan(args):
    """运行完整的4字母域名扫描"""
    log("开始全面扫描4字母.com域名...")
    log(f"使用配置: 线程数={args.threads}, API工作线程数={args.api_workers}")
    
    start_time = time.time()
    
    # 获取初始域名数量
    initial_checked, initial_available = get_domain_counts()
    log(f"初始状态：已检查域名 {initial_checked}，可用域名 {initial_available}")
    
    # 确定扫描的前缀
    if args.prefix:
        # 用户指定了特定前缀
        prefixes = [args.prefix]
        log(f"使用用户指定的前缀: {args.prefix}")
    elif args.prefix_file:
        # 从文件加载前缀
        try:
            with open(args.prefix_file, 'r') as f:
                prefixes = [line.strip() for line in f if line.strip()]
            log(f"从文件 {args.prefix_file} 加载了 {len(prefixes)} 个前缀")
        except Exception as e:
            log(f"无法读取前缀文件: {str(e)}，将使用默认前缀")
            prefixes = generate_prefixes()
    else:
        # 使用默认生成的前缀
        prefixes = generate_prefixes()
    
    total_prefixes = len(prefixes)
    log(f"共有 {total_prefixes} 个前缀需要扫描")
    
    # 已处理和跳过的前缀记录
    processed_prefixes = set()
    
    # 如果有进度文件且不是重新开始，加载已处理的前缀
    if os.path.exists('full_scan_progress.csv') and not args.restart:
        try:
            with open('full_scan_progress.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    processed_prefixes.add(row['prefix'])
            log(f"从进度文件中加载了 {len(processed_prefixes)} 个已处理的前缀")
        except:
            log("无法读取进度文件，将从头开始扫描")
    
    # 总进度跟踪
    total_prefixes_to_process = total_prefixes - len(processed_prefixes)
    if total_prefixes_to_process == 0:
        log("所有前缀已处理完毕！将重新扫描...")
        processed_prefixes.clear()
        total_prefixes_to_process = total_prefixes
    
    processed_count = 0
    
    # 遍历所有前缀
    for i, prefix in enumerate(prefixes, 1):
        # 如果已经处理过且不是强制模式，跳过
        if prefix in processed_prefixes and not args.force:
            continue
        
        prefix_start_time = time.time()
        processed_count += 1
        
        log(f"--------------------------------------------------")
        log(f"正在处理前缀 [{processed_count}/{total_prefixes_to_process}]: '{prefix}'")
        
        # 计算剩余长度
        remaining_length = 4 - len(prefix)
        
        # 构建命令参数
        cmd_args = [
            '--letters',
            '--length', '4',
            '--prefix', prefix,
            '--limit', str(args.limit),  # 使用用户指定的限制
            '--threads', str(args.threads),
            '--tld', '.com'
        ]
        
        # 如果需要立即进行API验证
        if args.verify_api:
            cmd_args.append('--verify-api')
            cmd_args.extend(['--api-workers', str(args.api_workers)])
        
        # 执行检查
        success = run_domain_checker(cmd_args, timeout=args.timeout)  # 用户指定的超时
        
        # 记录批次信息
        checked, available = get_domain_counts()
        duration = time.time() - prefix_start_time
        
        batch_info = {
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'prefix': prefix,
            'success': success,
            'checked_count': checked,
            'available_count': available,
            'duration': round(duration, 2)
        }
        
        save_batch_progress(batch_info)
        
        log(f"前缀完成: 已检查 {checked} 个域名，发现 {available} 个可用域名")
        log(f"耗时: {round(duration, 2)}秒")
        
        # 计算平均速度和预计剩余时间
        avg_time_per_prefix = duration
        remaining_prefixes = total_prefixes_to_process - processed_count
        estimated_time = avg_time_per_prefix * remaining_prefixes / 60  # 分钟
        
        log(f"平均每个前缀耗时: {round(avg_time_per_prefix, 2)}秒")
        log(f"预计剩余时间: {round(estimated_time, 2)}分钟")
        
        # 打印总体进度
        print_progress_bar(processed_count, total_prefixes_to_process, 
                       prefix='总进度:', suffix=f'完成 {processed_count}/{total_prefixes_to_process}')
        
        # 每次检查后暂停，避免过快请求
        log(f"暂停{args.pause}秒...")
        time.sleep(args.pause)
    
    # 如果需要最后进行API验证
    if not args.verify_api and args.final_verify:
        log("--------------------------------------------------")
        log("所有前缀扫描完成，开始API验证...")
        
        api_start_time = time.time()
        api_cmd_args = [
            '--only-verify-api', 
            '--api-workers', str(args.api_workers)
        ]
        
        api_success = run_domain_checker(api_cmd_args, timeout=7200)  # 2小时超时
        
        api_duration = time.time() - api_start_time
        log(f"API验证完成，耗时: {round(api_duration/60, 2)}分钟")
    
    # 最终汇总
    final_checked, final_available = get_domain_counts()
    total_duration = time.time() - start_time
    
    log("==================================================")
    log("全面扫描完成！")
    log(f"总耗时: {round(total_duration/3600, 2)}小时")
    log(f"总检查域名: {final_checked} (新增 {final_checked - initial_checked})")
    log(f"总可用域名: {final_available} (新增 {final_available - initial_available})")
    log("==================================================")
    
    # 显示或导出可用域名列表
    export_results()
    
    return True

def export_results():
    """导出扫描结果"""
    if not os.path.exists('available_domains.csv'):
        log("未找到可用域名文件")
        return
    
    try:
        # 读取可用域名
        with open('available_domains.csv', 'r') as f:
            domains = [line.strip() for line in f]
        
        # 按字母排序
        domains.sort()
        
        # 写入排序后的结果文件
        with open('sorted_available_domains.csv', 'w') as f:
            for domain in domains:
                f.write(f"{domain}\n")
        
        log(f"共找到 {len(domains)} 个可用域名，已排序并保存到 sorted_available_domains.csv")
        
        # 如果数量不多则显示
        if len(domains) < 100:
            log("可用域名列表:")
            for domain in domains:
                log(f"  {domain}")
        
    except Exception as e:
        log(f"导出结果时出错: {str(e)}")

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

def cleanup():
    """清理函数，在程序终止时调用"""
    log("程序终止，正在清理资源...")
    # 这里可以添加任何需要的清理代码

def setup_signal_handlers():
    """设置信号处理器"""
    # 注册清理函数
    atexit.register(cleanup)
    
    # 处理SIGINT（Ctrl+C）
    def sigint_handler(sig, frame):
        log("收到中断信号，正在优雅退出...")
        sys.exit(0)
    
    try:
        signal.signal(signal.SIGINT, sigint_handler)
    except (AttributeError, ValueError):
        # 某些平台可能不支持
        pass

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='四字母域名全面扫描工具')
    
    # 扫描控制
    parser.add_argument('--prefix', help='指定要扫描的单个前缀')
    parser.add_argument('--prefix-file', help='包含要扫描的前缀列表的文件')
    parser.add_argument('--limit', type=int, default=100000, help='每个前缀的域名数量限制 (默认: 100000)')
    parser.add_argument('--threads', type=int, default=50, help='DNS检查的并发线程数 (默认: 50)')
    parser.add_argument('--timeout', type=int, default=1200, help='每个前缀的超时时间(秒) (默认: 1200)')
    parser.add_argument('--pause', type=int, default=5, help='每个前缀间的暂停时间(秒) (默认: 5)')
    
    # API验证相关
    parser.add_argument('--verify-api', action='store_true', help='在DNS检查时直接进行API验证')
    parser.add_argument('--final-verify', action='store_true', help='扫描结束后进行API验证')
    parser.add_argument('--api-workers', type=int, default=1, help='API验证的并发工作线程数 (默认: 1)')
    
    # 其他选项
    parser.add_argument('--restart', action='store_true', help='重新开始扫描，忽略之前的进度')
    parser.add_argument('--force', action='store_true', help='强制重新检查所有前缀，包括已处理的')
    
    return parser.parse_args()

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 创建日志目录
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 初始化日志文件
    log_file = f"logs/full_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open('full_scan.log', 'w') as f:
        f.write(f"==== 四字母域名全面扫描 开始于 {datetime.datetime.now()} ====\n\n")
    
    # 设置信号处理
    setup_signal_handlers()
    
    print("=" * 80)
    print("  四字母域名全面扫描工具")
    print("=" * 80)
    print("此脚本将扫描所有可能的4字母.com域名")
    print("扫描可能需要较长时间，您可以随时按Ctrl+C中断")
    print("中断后重启脚本将从上次中断处继续")
    print("=" * 80)
    
    if not check_environment():
        log("环境检查未通过，程序无法运行")
        return 1
    
    try:
        # 运行全面扫描
        run_full_scan(args)
    except KeyboardInterrupt:
        log("用户中断了扫描")
    except Exception as e:
        log(f"扫描过程中出错: {str(e)}")
        import traceback
        log(traceback.format_exc())
        return 1
    
    log("程序执行完毕")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 