#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Finder 基本使用示例
"""

import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入核心组件
from domain_finder import (
    generate_domains,
    dns_check,
    load_checked_domains,
    save_checked_domains,
    save_available_domain
)

def main():
    """示例：如何使用Domain Finder的核心功能"""
    print("Domain Finder 基本使用示例")
    print("-" * 50)
    
    # 1. 生成一些测试域名
    print("生成测试域名...")
    domains = generate_domains(
        characters="abcde",
        length=3,
        limit=10,
        prefix="test",
        suffix="",
        tld=".com"
    )
    
    print(f"生成了 {len(domains)} 个域名:")
    for domain in domains:
        print(f"  - {domain}")
    
    print("-" * 50)
    
    # 2. 对这些域名进行DNS检查
    print("执行DNS检查...")
    results = []
    
    for domain in domains:
        domain, is_registered, error = dns_check(domain)
        
        status = "已注册" if is_registered else "可能可用"
        if error:
            status += f" (错误: {error})"
        
        print(f"  - {domain}: {status}")
        
        # 将结果添加到列表中
        row = {
            "domain": domain,
            "dns_checked": True,
            "api_verified": False,
            "available": not is_registered,
            "note": error if error else ("已注册" if is_registered else "DNS无记录，可能可用")
        }
        results.append(row)
    
    print("-" * 50)
    
    # 3. 保存结果示例
    print("这些结果通常会保存到CSV文件中...")
    print("可用的域名会单独记录到available_domains.csv文件中")
    
    # 实际使用Domain Finder时，这些操作会自动完成
    print("-" * 50)
    
    # 4. 如何在实际项目中使用
    print("实际使用示例:")
    print("1. 配置API (复制config.json.example为config.json并填入API密钥)")
    print("2. 运行命令行工具:")
    print("   python domain_finder.py --characters abcde --limit 100 --verify-api")
    print("3. 查看结果文件 available_domains.csv")

if __name__ == "__main__":
    main() 