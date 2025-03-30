#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Finder - 命令行界面
Command Line Interface for Domain Finder

作者/Author: Alan
"""

import os
import sys
import time
import subprocess
import signal
import csv
from datetime import datetime

# 尝试导入语言配置模块
try:
    from language_config import get_text, get_language
except ImportError:
    # 定义简易替代函数，如果模块不存在
    def get_language():
        return os.environ.get("DOMAIN_FINDER_LANG", "zh")
    
    def get_text(key, lang=None):
        # 简单的中英文文本映射
        zh_texts = {
            "title": "域名查找工具",
            "menu_basic": "基本域名检查",
            "menu_api": "带API验证的域名检查",
            "menu_high_perf": "高性能检查",
            "menu_custom": "自定义命令",
            "menu_view": "查看已发现可用域名",
            "menu_exit": "退出",
            "prompt_option": "请输入选项 [1-6]: ",
            "invalid_option": "无效选项，请重新输入",
            "thank_you": "谢谢使用域名查找工具！",
            "custom_prompt": "请输入命令参数: ",
            "no_results": "没有找到可用域名记录",
            "running_command": "执行命令",
            "command_complete": "命令执行完成",
            "command_failed": "命令执行失败",
            "available_domains": "可用域名列表",
            "domain": "域名",
            "check_time": "检查时间",
            "notes": "备注",
            "continue_prompt": "按Enter继续...",
        }
        
        en_texts = {
            "title": "Domain Finder Tool",
            "menu_basic": "Basic Domain Check",
            "menu_api": "API Verification Check",
            "menu_high_perf": "High Performance Check",
            "menu_custom": "Custom Command",
            "menu_view": "View Available Domains",
            "menu_exit": "Exit",
            "prompt_option": "Please enter option [1-6]: ",
            "invalid_option": "Invalid option, please try again",
            "thank_you": "Thank you for using Domain Finder Tool!",
            "custom_prompt": "Enter command parameters: ",
            "no_results": "No available domain records found",
            "running_command": "Running command",
            "command_complete": "Command completed",
            "command_failed": "Command execution failed",
            "available_domains": "Available Domains List",
            "domain": "Domain",
            "check_time": "Check Time",
            "notes": "Notes",
            "continue_prompt": "Press Enter to continue...",
        }
        
        lang = lang or get_language()
        if lang == "zh":
            return zh_texts.get(key, key)
        else:
            return en_texts.get(key, key)

def print_header():
    """打印标题头部 / Print header"""
    print("\n" + "=" * 80)
    if get_language() == "zh":
        print(f"  {get_text('title')} - Apple M2 版本")
    else:
        print(f"  {get_text('title')} - Apple M2 Version")
    print("=" * 80)

def print_menu():
    """打印主菜单 / Print main menu"""
    print("\n选择操作：" if get_language() == "zh" else "\nSelect operation:")
    print(f"1. {get_text('menu_basic')} (--letters --length 4 --limit 100)")
    print(f"2. {get_text('menu_api')} (--verify-api)")
    print(f"3. {get_text('menu_high_perf')} (--threads 50)")
    print(f"4. {get_text('menu_custom')}")
    print(f"5. {get_text('menu_view')}")
    print(f"6. {get_text('menu_exit')}")
    
    return input(f"{get_text('prompt_option')}")

def run_command(cmd_args):
    """
    运行域名查找命令
    Run domain finder command
    
    Args:
        cmd_args: 命令行参数 / Command line arguments
    
    Returns:
        bool: 命令是否成功执行 / Whether the command was executed successfully
    """
    full_cmd = f"python3 domain_finder.py {cmd_args}"
    print(f"\n{get_text('running_command')}: {full_cmd}")
    
    try:
        result = subprocess.run(full_cmd, shell=True)
        if result.returncode == 0:
            print(f"\n{get_text('command_complete')}")
            return True
        else:
            print(f"\n{get_text('command_failed')} (code: {result.returncode})")
            return False
    except Exception as e:
        print(f"\n{get_text('command_failed')}: {str(e)}")
        return False

def view_available_domains():
    """
    查看可用域名列表
    View available domains list
    """
    available_file = 'available_domains.csv'
    
    if not os.path.exists(available_file):
        print(f"\n{get_text('no_results')}")
        return
    
    try:
        domains = []
        with open(available_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    domains.append(row)
        
        if not domains:
            print(f"\n{get_text('no_results')}")
            return
        
        print(f"\n{get_text('available_domains')}:")
        print(f"{'=' * 70}")
        print(f"{get_text('domain'):<30} | {get_text('check_time'):<20} | {get_text('notes')}")
        print(f"{'-' * 30}---{'-' * 20}---{'-' * 20}")
        
        for domain, check_time, note in domains:
            print(f"{domain:<30} | {check_time:<20} | {note}")
        
        print(f"{'=' * 70}")
        print(f"总计: {len(domains)}个域名" if get_language() == "zh" else f"Total: {len(domains)} domains")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    input(f"\n{get_text('continue_prompt')}")

def main():
    """主函数 / Main function"""
    # 处理Ctrl+C / Handle Ctrl+C
    def signal_handler(sig, frame):
        print(f"\n\n{get_text('thank_you')}")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        print_header()
        choice = print_menu()
        
        if choice == '1':
            run_command("--letters --length 4 --limit 100")
        elif choice == '2':
            run_command("--letters --length 4 --limit 50 --verify-api")
        elif choice == '3':
            run_command("--letters --length 4 --limit 500 --threads 50")
        elif choice == '4':
            custom_cmd = input(f"\n{get_text('custom_prompt')}")
            run_command(custom_cmd)
        elif choice == '5':
            view_available_domains()
        elif choice == '6':
            print(f"\n{get_text('thank_you')}")
            break
        else:
            print(f"\n{get_text('invalid_option')}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        # 设置双语支持
        lang = os.environ.get("DOMAIN_FINDER_LANG", "zh")
        if len(sys.argv) > 1 and sys.argv[1].startswith("--lang="):
            lang = sys.argv[1].split("=")[1]
            os.environ["DOMAIN_FINDER_LANG"] = lang
        
        main()
    except KeyboardInterrupt:
        print(f"\n{get_text('thank_you')}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 