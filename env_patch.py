#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境修补模块 / Environment Patch Module

此模块用于解决macOS版本检测问题，特别是在Apple Silicon芯片上
This module addresses macOS version detection issues, especially on Apple Silicon chips

作者/Author: Alan
"""

import os
import sys
import platform
import subprocess
import builtins
import ctypes
from functools import wraps

# 保存原始函数 / Save original functions
_original_platform_mac_ver = platform.mac_ver
_original_platform_platform = platform.platform
_original_run = subprocess.run
_original_getattr = builtins.__getattribute__
_original___lt__ = str.__lt__
_original___le__ = str.__le__
_original___gt__ = str.__gt__
_original___ge__ = str.__ge__

# 设置版本号常量 / Set version number constants
TARGET_MACOS_VERSION = '14.7.0'
TARGET_BUILD_NUMBER = '14.7.0'

def disable_version_check():
    """
    禁用macOS版本检查，将版本修改为兼容值
    Disable macOS version check by modifying version to a compatible value
    """
    # 修改platform.mac_ver函数 / Patch platform.mac_ver function
    def patched_mac_ver():
        release, versioninfo, machine = _original_platform_mac_ver()
        
        # 对于所有macOS，修改版本号为14.7.0
        # For all macOS, modify version to 14.7.0
        if sys.platform == 'darwin':
            patched_release = TARGET_MACOS_VERSION
            print(f"环境修补已应用，macOS版本已修改为 {patched_release}")
            return (patched_release, versioninfo, machine)
        
        return (release, versioninfo, machine)
    
    # 修改platform.platform函数 / Patch platform.platform function
    def patched_platform(*args, **kwargs):
        result = _original_platform_platform(*args, **kwargs)
        if sys.platform == 'darwin' and 'macOS' in result:
            parts = result.split(' ')
            for i, part in enumerate(parts):
                if part.startswith('macOS-'):
                    parts[i] = f'macOS-{TARGET_MACOS_VERSION}'
            return ' '.join(parts)
        return result
    
    # 替换版本比较操作 / Replace version comparison operations
    # 创建一个通用的版本比较拦截器 / Create a generic version comparison interceptor
    def intercept_version_comparison(op_name, original_op):
        @wraps(original_op)
        def wrapper(a, b):
            # 检查是否可能是版本号比较
            if (isinstance(a, str) and isinstance(b, str) and 
                a.count('.') >= 2 and b.count('.') >= 2 and
                '14.' in (a + b)):
                
                # 根据操作符返回兼容结果
                if op_name == '__lt__':  # <
                    return False if '14.' in b else True
                elif op_name == '__le__':  # <=
                    return True if '14.' in b else False
                elif op_name == '__gt__':  # >
                    return True if '14.' in a else False
                elif op_name == '__ge__':  # >=
                    return True if '14.' in a else False
            
            # 其他情况使用原始操作符
            return original_op(a, b)
        return wrapper
    
    # 应用所有修补 / Apply all patches
    if sys.platform == 'darwin':
        platform.mac_ver = patched_mac_ver
        platform.platform = patched_platform
        
        # 拦截模块级别的比较操作 / Intercept module-level comparison operations
        # 替换 operator 模块中的比较函数 / Replace comparison functions in operator module
        import operator
        
        # 保存原始操作符函数 / Save original operator functions
        _original_lt = operator.lt
        _original_le = operator.le
        _original_gt = operator.gt
        _original_ge = operator.ge
        
        # 替换操作符函数 / Replace operator functions
        operator.lt = intercept_version_comparison('__lt__', _original_lt)
        operator.le = intercept_version_comparison('__le__', _original_le)
        operator.gt = intercept_version_comparison('__gt__', _original_gt)
        operator.ge = intercept_version_comparison('__ge__', _original_ge)
    
    # 修补subprocess.run以解决可能的进程问题 / Patch subprocess.run to fix potential process issues
    @wraps(subprocess.run)
    def _patched_run(cmd, *args, **kwargs):
        # 添加环境变量来禁用版本检查 / Add environment variable to disable version check
        env = kwargs.get('env', os.environ.copy())
        env['SYSTEM_VERSION_COMPAT'] = '1'
        
        # 设置PYTHONPATH环境变量 / Set PYTHONPATH environment variable
        current_path = os.getcwd()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{current_path}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = current_path
            
        kwargs['env'] = env
        
        return _original_run(cmd, *args, **kwargs)
    
    # 应用subprocess修补 / Apply subprocess patch
    subprocess.run = _patched_run
    
    # 设置环境变量 / Set environment variable
    os.environ['SYSTEM_VERSION_COMPAT'] = '1'
    
    # 尝试拦截版本比较 / Try to intercept version comparison
    try:
        if sys.platform == 'darwin':
            # 设置更多环境变量 / Set more environment variables
            os.environ['SYSTEM_VERSION_COMPAT'] = '1'
            # 如果使用了第三方库如distutils，也设置相关环境变量
            os.environ['MACOSX_DEPLOYMENT_TARGET'] = TARGET_MACOS_VERSION
    except Exception as e:
        print(f"高级修补失败: {e}")

# 自动应用修补 / Automatically apply patch
disable_version_check()

if __name__ == "__main__":
    # 如果直接运行这个脚本，打印状态信息 / If this script is run directly, print status
    print("环境修补成功应用！/ Environment patch successfully applied!")
    print(f"修补后的macOS版本: {platform.mac_ver()[0]}")
    print(f"系统环境: {platform.platform()}")
    
    # 测试版本号比较 / Test version number comparison
    import operator
    print("\n测试版本号比较: / Testing version comparison:")
    ver1 = "10.15.7"
    ver2 = "14.7.0"
    print(f"{ver1} < {ver2} (operator): {operator.lt(ver1, ver2)}")
    print(f"{ver1} <= {ver2} (operator): {operator.le(ver1, ver2)}")
    print(f"{ver1} > {ver2} (operator): {operator.gt(ver1, ver2)}")
    print(f"{ver1} >= {ver2} (operator): {operator.ge(ver1, ver2)}")
    print(f"{ver2} < {ver1} (operator): {operator.lt(ver2, ver1)}")
    print(f"{ver2} <= {ver1} (operator): {operator.le(ver2, ver1)}")
    print(f"{ver2} > {ver1} (operator): {operator.gt(ver2, ver1)}")
    print(f"{ver2} >= {ver1} (operator): {operator.ge(ver2, ver1)}")
