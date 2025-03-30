#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名查找器 - 纯命令行界面版本
此版本跳过所有系统版本检查，直接运行核心功能
"""

import os
import sys
import platform
import subprocess
import signal
import time
import argparse

# 设置环境变量跳过系统版本检查
os.environ['SYSTEM_VERSION_COMPAT'] = '1'

def print_header():
    """打印程序头部信息"""
    print("=" * 80)
    print("  四字母域名智能可注册性检测工具 - 通用版")
    print("=" * 80)

def get_available_domains():
    """获取已发现的可用域名"""
    if not os.path.exists('available_domains.csv'):
        print("未找到可用域名记录文件。请先运行域名检查。")
        return

    print("\n已发现的可用域名:")
    print("-" * 40)
    try:
        with open('available_domains.csv', 'r') as f:
            domains = f.readlines()
            for domain in domains:
                print(domain.strip())
        print("-" * 40)
        print(f"共找到 {len(domains)} 个可能可用的域名")
    except Exception as e:
        print(f"读取域名文件时出错: {str(e)}")

def run_domain_checker(args):
    """运行域名检查器"""
    cmd = [sys.executable, 'domain_finder.py'] + args
    print(f"\n执行命令: {' '.join(cmd)}\n")
    
    try:
        # 直接执行并将输出传递到当前控制台
        process = subprocess.Popen(cmd)
        
        # 等待进程完成
        process.wait()
        
        if process.returncode != 0:
            print(f"域名检查器异常退出，返回码: {process.returncode}")
            return False
        else:
            print("域名检查器已完成运行")
            return True
            
    except KeyboardInterrupt:
        print("\n用户中断操作...")
        return False
    except Exception as e:
        print(f"执行域名检查器时出错: {str(e)}")
        return False

def run_cli():
    """运行命令行界面"""
    print_header()
    
    while True:
        print("\n选择操作：")
        print("1. 基本域名检查 (--letters --length 4 --limit 100)")
        print("2. 带API验证的域名检查 (--verify-api)")
        print("3. 高性能检查 (--threads 50)")
        print("4. 自定义命令")
        print("5. 查看已发现可用域名")
        print("6. 批量自动检查 (先基本检查，然后API验证)")
        print("7. 退出")
        
        try:
            choice = input("请输入选项 [1-7]: ").strip()
            
            if choice == '1':
                run_domain_checker(['--letters', '--length', '4', '--limit', '100'])
            elif choice == '2':
                run_domain_checker(['--letters', '--length', '4', '--limit', '50', '--verify-api'])
            elif choice == '3':
                run_domain_checker(['--letters', '--length', '4', '--limit', '200', '--threads', '50'])
            elif choice == '4':
                custom_args = input("请输入自定义参数 (例如: --letters --length 3 --limit 50): ").strip()
                if custom_args:
                    run_domain_checker(custom_args.split())
                else:
                    print("未提供参数，操作取消")
            elif choice == '5':
                get_available_domains()
            elif choice == '6':
                run_auto_batch()
            elif choice == '7':
                print("谢谢使用域名查找工具！")
                return True
            else:
                print("无效选项，请重新选择")
                
        except KeyboardInterrupt:
            print("\n谢谢使用域名查找工具！")
            return True
        except Exception as e:
            print(f"发生错误: {str(e)}")
    
    return True

def run_auto_batch():
    """运行自动批量检查"""
    print("\n开始自动批量检查流程...")
    
    # 1. 先运行多组基本检查以收集潜在可用域名
    lengths = [3, 4]
    batches = [100, 200, 300]
    
    for length in lengths:
        for batch in batches:
            print(f"\n[自动批量] 正在检查长度为{length}的域名，批次大小: {batch}")
            success = run_domain_checker(['--letters', '--length', str(length), '--limit', str(batch), '--threads', '50'])
            if not success:
                print("基本检查失败，跳过该批次")
                continue
            
            # 每次检查后暂停几秒，避免过于频繁的请求
            print("暂停5秒...")
            time.sleep(5)
    
    # 2. 对收集到的可用域名进行API验证
    print("\n[自动批量] 所有基本检查完成，开始API验证...")
    
    # 直接使用only-verify-api参数验证之前找到的所有域名
    run_domain_checker(['--only-verify-api', '--api-workers', '1'])
    
    # 3. 显示最终结果
    print("\n[自动批量] 所有检查完成！最终结果:")
    get_available_domains()
    
    return True

def check_environment():
    """检查运行环境"""
    print(f"系统: {platform.system()} {platform.release()}")
    print(f"Python版本: {platform.python_version()}")
    print(f"处理器架构: {platform.machine()}")
    
    # 检查必要文件
    if not os.path.exists('domain_finder.py'):
        print("错误: 无法找到核心文件 domain_finder.py")
        return False
    
    return True

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='域名查找工具 - 命令行版本')
    parser.add_argument('--auto', action='store_true', help='自动执行批量检查，无需用户交互')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    if not check_environment():
        print("环境检查未通过，程序无法运行")
        return 1
    
    # 设置信号处理
    try:
        signal.signal(signal.SIGINT, lambda sig, frame: None)
    except (AttributeError, ValueError):
        pass  # 忽略Windows平台不支持的信号
    
    # 如果指定了自动模式，直接运行批量检查
    if args.auto:
        print("自动模式启动，开始批量检查...")
        run_auto_batch()
        return 0
    
    # 否则运行交互式CLI界面
    cli_success = run_cli()
    
    if not cli_success:
        print("命令行界面异常退出")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 