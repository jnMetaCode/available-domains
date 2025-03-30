# 安装指南 / Installation Guide

[English](#installation-guide) | [中文](#安装指南)

## 安装指南

### 系统要求

- Python 3.8 或更高版本
- macOS Monterey(12.0)或更高版本（对于GUI界面）
- 支持Apple Silicon芯片(M1/M2/M3)和Intel芯片

### 从源码安装

1. 克隆仓库
```bash
git clone https://github.com/jnMetaCode/domain-finder.git
cd domain-finder
```

2. 创建虚拟环境并激活
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置
```bash
cp config.json.example config.json
# 编辑config.json，填入你的API密钥和设置
```

### 运行应用

使用启动脚本运行应用：
```bash
./run_app.sh
```

指定语言（可选）：
```bash
./run_app.sh --lang=zh  # 中文界面
./run_app.sh --lang=en  # 英文界面
```

### M系列芯片特殊说明

如果在M系列芯片上遇到SSL相关的错误，可以使用环境修补工具：
```bash
python3 env_patch.py
```

然后再使用启动脚本：
```bash
./run_app.sh
```

---

## Installation Guide

### System Requirements

- Python 3.8 or higher
- macOS Monterey(12.0) or higher (for GUI interface)
- Supports both Apple Silicon chips (M1/M2/M3) and Intel chips

### Install from Source

1. Clone the repository
```bash
git clone https://github.com/jnMetaCode/domain-finder.git
cd domain-finder
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure
```bash
cp config.json.example config.json
# Edit config.json to add your API keys and settings
```

### Run the Application

Use the startup script to run the application:
```bash
./run_app.sh
```

Specify language (optional):
```bash
./run_app.sh --lang=zh  # Chinese interface
./run_app.sh --lang=en  # English interface
```

### M-series Chip Special Notes

If you encounter SSL-related errors on M-series chips, you can use the environment patching tool:
```bash
python3 env_patch.py
```

Then use the startup script:
```bash
./run_app.sh
``` 