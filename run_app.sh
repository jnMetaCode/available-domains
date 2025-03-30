#!/bin/bash
# 域名查找工具智能启动脚本 / Domain Finder Smart Launch Script
# 自动选择适合当前环境的界面版本，支持中英文切换
# Automatically selects the appropriate interface version and supports language switching

# 设置默认语言 / Set default language
LANGUAGE=${LANGUAGE:-"zh"}  # 默认中文 / Default to Chinese

# 检测颜色支持 / Detect color support
if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN=''
  YELLOW=''
  BLUE=''
  RED=''
  BOLD=''
  NC=''
fi

# 双语提示函数 / Bilingual message function
show_message() {
  local zh_msg="$1"
  local en_msg="$2"
  local type="$3"
  
  if [ "$LANGUAGE" = "zh" ]; then
    local msg="$zh_msg"
  else
    local msg="$en_msg"
  fi
  
  case "$type" in
    "success") echo -e "${GREEN}✓ ${msg}${NC}" ;;
    "info")    echo -e "${BLUE}${BOLD}${msg}${NC}" ;;
    "warning") echo -e "${YELLOW}! ${msg}${NC}" ;;
    "error")   echo -e "${RED}✗ ${msg}${NC}" ;;
    *)         echo -e "${msg}" ;;
  esac
}

# 处理参数 / Process arguments
for arg in "$@"; do
  case $arg in
    --lang=*)
      LANGUAGE="${arg#*=}"
      if [ "$LANGUAGE" != "zh" ] && [ "$LANGUAGE" != "en" ]; then
        show_message "不支持的语言: $LANGUAGE，使用默认语言中文" "Unsupported language: $LANGUAGE, using default Chinese" "warning"
        LANGUAGE="zh"
      fi
      ;;
    --help|-h)
      show_message "用法: ./run_app.sh [选项]
选项:
  --lang=zh|en    设置界面语言（中文或英文）
  --help, -h      显示此帮助信息" "Usage: ./run_app.sh [options]
Options:
  --lang=zh|en    Set interface language (Chinese or English)
  --help, -h      Show this help message" "info"
      exit 0
      ;;
  esac
done

show_message "当前界面语言: ${LANGUAGE}" "Current interface language: ${LANGUAGE}" "success"

# 检测平台和芯片 / Detect platform and chip
is_apple_silicon=false
if [[ $(uname) == "Darwin" && $(uname -m) == "arm64" ]]; then
  is_apple_silicon=true
  show_message "检测到Apple Silicon芯片" "Apple Silicon chip detected" "success"
fi

# 检查macOS版本 / Check macOS version
if [[ $(uname) == "Darwin" ]]; then
  macos_version=$(sw_vers -productVersion)
  show_message "macOS版本: ${macos_version}" "macOS version: ${macos_version}" "success"
fi

# 获取Python版本 / Get Python version
python_version=$(python3 --version 2>&1)
show_message "Python版本: ${python_version}" "Python version: ${python_version}" "success"

# 设置环境变量 / Set environment variables
export DOMAIN_FINDER_LANG="$LANGUAGE"
export PYTHONPATH="$PWD:$PYTHONPATH"
export SYSTEM_VERSION_COMPAT=1

# 应用环境修补 / Apply environment patch
show_message "应用环境修补..." "Applying environment patch..." "info"

# 运行环境修补脚本 / Run environment patch script
if [ -f "env_patch.py" ]; then
  python3 -c "from env_patch import disable_version_check; disable_version_check()"
  if [ $? -ne 0 ]; then
    show_message "环境修补应用失败" "Environment patch application failed" "error"
  fi
else
  show_message "找不到环境修补文件，部分功能可能不可用" "Environment patch file not found, some features may not be available" "warning"
fi

# 创建修补后的启动命令 / Create patched launch command
create_python_launcher() {
  cat > .run_helper.py << EOF
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行助手 - 在执行任何导入前应用环境修补
Run Helper - Apply environment patch before any imports
"""

import os
import sys
import importlib.util

def pre_import_patch():
    """优先应用所有环境修补"""
    # 首先检查并导入env_patch模块
    try:
        # 直接从字节码导入env_patch模块
        if os.path.exists('env_patch.py'):
            # 添加当前目录到路径
            sys.path.insert(0, os.getcwd())
            
            # 强制应用环境修补
            spec = importlib.util.spec_from_file_location("env_patch", "env_patch.py")
            env_patch = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(env_patch)
            
            # 调用函数禁用版本检查
            if hasattr(env_patch, 'disable_version_check'):
                env_patch.disable_version_check()
                return True
    except Exception as e:
        print(f"警告: 无法应用环境修补: {e}")
    return False

def run_target_module(module_name):
    """运行指定的模块"""
    try:
        # 动态导入目标模块
        target_module = __import__(module_name)
        
        # 如果模块有main函数，调用它
        if hasattr(target_module, 'main'):
            target_module.main()
        else:
            print(f"错误: {module_name} 模块没有 main 函数")
            return False
        return True
    except ImportError:
        print(f"错误: 无法导入模块 {module_name}")
        return False
    except Exception as e:
        print(f"错误: 运行 {module_name} 时发生错误: {e}")
        return False

if __name__ == "__main__":
    # 如果提供了参数，使用第一个参数作为模块名
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        # 首先应用环境修补
        pre_import_patch()
        # 然后运行目标模块
        run_target_module(module_name)
    else:
        print("错误: 未指定目标模块")
        sys.exit(1)
EOF
  chmod +x .run_helper.py
  show_message "创建启动辅助脚本" "Created launch helper script" "success"
}

# 创建启动辅助脚本 / Create launch helper script
create_python_launcher

# 尝试启动应用 / Try to launch application
show_message "正在启动域名查找工具..." "Launching Domain Finder Tool..." "info"

# 尝试启动顺序 / Launch attempt sequence
launch_successful=false

# 1. 简化版GUI (M系列芯片优先) / Simplified GUI (M series chip priority)
if [ -f "run_gui_simplified.py" ]; then
  show_message "正在启动简化版GUI..." "Launching simplified GUI..." "info"
  python3 .run_helper.py run_gui_simplified && launch_successful=true
fi

# 2. 命令行界面 / Command line interface
if [ "$launch_successful" = false ] && [ -f "run_m2.py" ]; then
  show_message "尝试启动命令行界面..." "Trying to launch command line interface..." "info"
  python3 .run_helper.py run_m2 && launch_successful=true
fi

# 3. 最后尝试核心功能 / Finally try core functionality
if [ "$launch_successful" = false ]; then
  show_message "界面启动失败，尝试核心功能..." "Interface launch failed, trying core functionality..." "error"
  show_message "使用以下命令检查域名:" "Use the following command to check domains:" "info"
  echo -e "${BOLD}python3 domain_finder.py --letters --length 4 --limit 100${NC}"
  
  # 显示简要帮助信息 / Show brief help information
  show_message "可用命令选项:" "Available command options:" "info"
  echo "--letters        使用所有字母 / Use all letters"
  echo "--digits         使用数字 / Use digits"
  echo "--length N       设置域名长度 / Set domain length"
  echo "--limit N        设置检查数量 / Set check limit"
  echo "--verify-api     使用API验证 / Use API verification"
fi

# 清理临时文件 / Clean up temporary files
if [ -f ".run_helper.py" ]; then
  rm .run_helper.py
fi 