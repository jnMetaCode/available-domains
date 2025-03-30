#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain Finder Package
"""

from .core import (
    generate_domains,
    dns_check,
    api_check,
    porkbun_check,
    dynadot_check,
    load_checked_domains,
    save_checked_domains,
    save_available_domain,
    log_error,
    APIConfig,
    Counter
)

__version__ = '0.1.0'
__author__ = 'Alan'

# 便于导入的组件列表
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
    'Counter',
    'main'  # 主程序入口
]

# 导入主程序入口
from .core import main 