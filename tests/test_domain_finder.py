#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入待测试模块
import domain_finder

class TestDomainFinder(unittest.TestCase):
    """域名查找工具测试类"""

    def setUp(self):
        """测试前设置"""
        self.finder = domain_finder.DomainFinder()
        
    def test_generate_domain_names(self):
        """测试域名生成功能"""
        # 测试字母域名生成
        domains = self.finder.generate_domain_names(
            length=2,
            use_letters=True,
            use_digits=False,
            use_symbols=False,
            limit=10
        )
        self.assertEqual(len(domains), 10)
        for domain in domains:
            self.assertEqual(len(domain), 2)
            self.assertTrue(all(c.isalpha() for c in domain))
        
        # 测试数字域名生成
        domains = self.finder.generate_domain_names(
            length=2,
            use_letters=False,
            use_digits=True,
            use_symbols=False,
            limit=10
        )
        self.assertEqual(len(domains), 10)
        for domain in domains:
            self.assertEqual(len(domain), 2)
            self.assertTrue(all(c.isdigit() for c in domain))

    def test_check_domain_dns(self):
        """测试DNS域名检查功能（模拟测试）"""
        # 这里仅创建测试结构，实际测试需要模拟DNS响应
        pass

    def test_check_domain_api(self):
        """测试API域名检查功能（模拟测试）"""
        # 这里仅创建测试结构，实际测试需要模拟API响应
        pass

if __name__ == '__main__':
    unittest.main() 