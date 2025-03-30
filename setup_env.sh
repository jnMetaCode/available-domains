#!/bin/bash
# 域名查找工具 - 环境设置脚本 (Apple Silicon)
# 此脚本为macOS 14.7+和Apple M2/M3芯片优化

# 检测颜色支持
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  BOLD=''
  NC=''
fi

echo -e "${BLUE}${BOLD}域名查找工具 - 环境设置${NC}"
echo -e "${BLUE}======================================${NC}"
echo

# 检查是否为Apple Silicon
if [[ $(uname -s) == "Darwin" && $(uname -m) == "arm64" ]]; then
  echo -e "${GREEN}✓ 检测到Apple Silicon架构${NC}"
else
  echo -e "${YELLOW}! 非Apple Silicon架构，某些优化可能不适用${NC}"
fi

# 检查Homebrew是否已安装
echo -e "\n${BOLD}检查Homebrew...${NC}"
if command -v brew &>/dev/null; then
  echo -e "${GREEN}✓ Homebrew已安装${NC}"
else
  echo -e "${YELLOW}! Homebrew未安装，正在安装...${NC}"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 检查并安装pyenv
echo -e "\n${BOLD}检查pyenv...${NC}"
if command -v pyenv &>/dev/null; then
  echo -e "${GREEN}✓ pyenv已安装${NC}"
else
  echo -e "${YELLOW}! pyenv未安装，正在安装...${NC}"
  brew update
  brew install pyenv
  
  # 添加pyenv到shell配置
  echo -e "\n${BOLD}配置pyenv环境...${NC}"
  echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
  echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
  echo 'eval "$(pyenv init -)"' >> ~/.zshrc
  
  echo -e "${YELLOW}! 请重新打开终端或运行 'source ~/.zshrc' 使配置生效${NC}"
  source ~/.zshrc
fi

# 安装Python 3.11.8
echo -e "\n${BOLD}检查Python 3.11.8...${NC}"
if pyenv versions | grep -q "3.11.8"; then
  echo -e "${GREEN}✓ Python 3.11.8已安装${NC}"
else
  echo -e "${YELLOW}! 正在安装Python 3.11.8 (带OpenSSL支持)...${NC}"
  
  # 安装依赖
  brew install openssl readline sqlite3 xz zlib
  
  # 设置编译环境以使用Homebrew的OpenSSL
  env \
    CPPFLAGS="-I$(brew --prefix openssl)/include" \
    LDFLAGS="-L$(brew --prefix openssl)/lib" \
    pyenv install 3.11.8
    
  echo -e "${GREEN}✓ Python 3.11.8安装完成${NC}"
fi

# 设置本地Python版本
echo -e "\n${BOLD}设置本地Python版本...${NC}"
pyenv local 3.11.8
echo -e "${GREEN}✓ 已将当前目录Python版本设置为3.11.8${NC}"

# 创建虚拟环境
echo -e "\n${BOLD}创建虚拟环境...${NC}"
if [ -d ".venv" ]; then
  echo -e "${YELLOW}! 虚拟环境已存在，跳过创建${NC}"
else
  python -m venv .venv
  echo -e "${GREEN}✓ 虚拟环境创建完成${NC}"
fi

# 激活虚拟环境
echo -e "\n${BOLD}激活虚拟环境...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ 虚拟环境已激活${NC}"

# 更新pip和安装核心依赖
echo -e "\n${BOLD}安装依赖...${NC}"
pip install -U pip setuptools wheel
echo -e "${GREEN}✓ 基础工具已更新${NC}"

# 创建更新的requirements文件
echo -e "\n${BOLD}创建兼容的requirements.txt...${NC}"
cat > requirements.txt << EOL
# 核心依赖
dnspython==2.4.2
requests>=2.28.0
urllib3==1.26.16  # 降级以避免LibreSSL兼容问题
pillow>=9.0.0

# GUI依赖
tk>=8.6.0

# 可选组件
pandas>=1.5.0
ttkthemes>=3.2.2  # 可选

# 打包依赖
pyinstaller>=5.9.0
EOL
echo -e "${GREEN}✓ requirements.txt已创建${NC}"

# 安装依赖
echo -e "\n${BOLD}安装项目依赖...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓ 所有依赖安装完成${NC}"

# 创建启动脚本
echo -e "\n${BOLD}创建启动脚本...${NC}"
cat > run_app.sh << EOL
#!/bin/bash
# 域名查找工具启动脚本

# 激活虚拟环境
source .venv/bin/activate

# 运行图形界面
echo "正在启动域名查找工具..."
python run_gui.py

# 如果GUI无法启动，提供后备方案
if [ \$? -ne 0 ]; then
  echo "GUI启动失败，尝试命令行界面..."
  python run_m2.py
fi
EOL
chmod +x run_app.sh
echo -e "${GREEN}✓ 启动脚本创建完成${NC}"

echo -e "\n${BLUE}${BOLD}环境设置完成!${NC}"
echo -e "${GREEN}------------------------------${NC}"
echo -e "运行以下命令启动应用："
echo -e "${BOLD}./run_app.sh${NC}"
echo
echo -e "${YELLOW}注意：每次打开新终端窗口都需要激活环境:${NC}"
echo -e "${BOLD}source .venv/bin/activate${NC}"
echo 