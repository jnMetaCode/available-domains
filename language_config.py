#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言配置模块 / Multilingual Configuration Module

此模块提供了域名查找工具的多语言支持功能
This module provides multilingual support for the Domain Finder tool

作者/Author: Alan
"""

import os

# 支持的语言 / Supported languages
SUPPORTED_LANGUAGES = ["zh", "en"]
DEFAULT_LANGUAGE = "zh"  # 默认中文 / Default to Chinese

# 获取当前语言设置 / Get current language setting
def get_language():
    """获取当前语言设置 / Get current language setting"""
    lang = os.environ.get("DOMAIN_FINDER_LANG", DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        print(f"不支持的语言设置: {lang}，使用默认中文 / "
              f"Unsupported language: {lang}, using default Chinese")
        return DEFAULT_LANGUAGE
    return lang

# 通用文本 / Common text
_TEXT = {
    "zh": {
        # 核心文本 / Core text
        "title": "域名查找工具",
        "subtitle": "高效的四字母域名查找工具",
        
        # 界面元素 / UI elements
        "btn_start": "开始",
        "btn_stop": "停止",
        "btn_reset": "重置",
        "btn_export": "导出",
        
        # 域名选项 / Domain options
        "domain_length": "域名长度",
        "domain_type": "域名类型",
        "domain_letters": "纯字母",
        "domain_digits": "纯数字",
        "domain_mixed": "字母数字混合",
        
        # 命令行界面文本 / CLI text
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
    },
    
    "en": {
        # Core text
        "title": "Domain Finder",
        "subtitle": "Efficient Four-letter Domain Lookup Tool",
        
        # UI elements
        "btn_start": "Start",
        "btn_stop": "Stop",
        "btn_reset": "Reset",
        "btn_export": "Export",
        
        # Domain options
        "domain_length": "Domain Length",
        "domain_type": "Domain Type",
        "domain_letters": "Letters Only",
        "domain_digits": "Digits Only",
        "domain_mixed": "Alphanumeric",
        
        # CLI text
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
}

def get_text(key, lang=None):
    """
    获取指定键的文本 / Get text for a specific key
    
    Args:
        key: 文本键 / Text key
        lang: 语言代码 / Language code (zh/en)
    
    Returns:
        str: 对应的文本 / Corresponding text
    """
    lang = lang or get_language()
    
    # 确保使用支持的语言 / Ensure using a supported language
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    # 返回请求的文本，如果不存在则返回键名 / Return requested text, or key if not found
    return _TEXT.get(lang, {}).get(key, key)

# 便于导入的函数和变量
__all__ = [
    'get_language',
    'get_text',
    'SUPPORTED_LANGUAGES',
    'DEFAULT_LANGUAGE'
]

if __name__ == "__main__":
    # 简单测试
    print(f"当前语言 / Current language: {get_language()}")
    print(f"标题文本 / Title text: {get_text('title')}")
    print(f"英文标题 / English title: {get_text('title', 'en')}") 