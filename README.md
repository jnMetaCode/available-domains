# 域名查找工具 / Domain Finder

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

一个功能强大的域名可用性检查工具，专为寻找可注册的短域名而设计。

[English Documentation](#english-documentation) | [中文文档](#中文文档)

![Domain Finder 截图](docs/screenshot.png)

## 中文文档

### 特性

- 🚀 **高性能并发检查** - 利用多线程技术快速检查大量域名
- 🔍 **多种查询方式** - 支持字母、数字或混合组合域名查询
- 🧰 **多种界面选择** - 提供GUI界面和命令行界面
- 🔄 **智能断点续传** - 支持大规模扫描的中断恢复
- 🌐 **API验证集成** - 支持多家域名注册商API验证
- 🍎 **Apple Silicon优化** - 针对M系列芯片优化的性能

### 安装

#### 要求

- Python 3.8 或更高版本
- macOS Monterey(12.0)或更高版本（对于GUI界面）
- 支持Apple Silicon芯片(M1/M2/M3)和Intel芯片

#### 从源码安装

```bash
# 克隆仓库
git clone https://github.com/jnMetaCode/domain-finder.git
cd domain-finder

# 创建虚拟环境并激活
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置
cp config.json.example config.json
# 编辑config.json，填入你的API密钥和设置
```

### 快速开始

1. 启动应用程序：

```bash
./run_app.sh
如：选择4,自定义
```

该脚本会自动选择最适合您系统的界面版本。

2. 选择语言（可选）：

```bash
./run_app.sh --lang=zh  # 中文界面
./run_app.sh --lang=en  # 英文界面
```
3. 操作

选择操作：
1. 基本域名检查 (--letters --length 4 --limit 100)
2. 带API验证的域名检查 (--verify-api)
3. 高性能检查 (--threads 50)
4. 自定义命令
5. 查看已发现可用域名
6. 退出
请输入选项 [1-6]: 4

请输入命令参数:--letters --length 4 --limit 456976 --verify-api --threads 30

###说明：扫描字母，4位数，全部，使用初步筛查：dns，使用精准核实：api ，dns线程：30


### 界面选项

#### 简化版GUI界面

简化版GUI界面提供了直观的图形操作环境，适合不熟悉命令行的用户：

- **域名长度**：设置要检查的域名长度
- **域名类型**：选择字母、数字或混合类型
- **检查数量**：设置检查的域名数量上限
- **线程数**：调整并发检查线程数
- **API验证**：勾选后将使用API验证域名可注册性

#### 命令行界面

命令行界面提供更多自定义选项，适合高级用户：

```bash
python3 domain_finder.py --letters --length 4 --limit 100
```

常用参数说明：
- `--letters`: 使用字母组合
- `--digits`: 使用数字组合
- `--alphanumeric`: 使用字母数字混合组合
- `--length N`: 设置域名长度
- `--limit N`: 限制检查数量
- `--threads N`: 设置线程数
- `--verify-api`: 使用API验证
- `--only-verify-api`: 仅执行API验证
- `--verbose`: 显示详细输出

### 全面扫描工具

对于需要检查所有可能的四字母域名的用户，我们提供了专门的全面扫描工具 `run_full_scan.py`：

```bash
# 完整扫描所有4字母域名
nohup python3 run_full_scan.py --final-verify > logs/full_scan.log 2>&1 &

# 同时进行DNS和API验证的扫描
nohup python3 run_full_scan.py --verify-api --threads 50 > logs/full_scan.log 2>&1 &

# 扫描特定前缀的域名
python3 run_full_scan.py --prefix "a" --limit 10000 --verify-api
```

其他：你希望：

✅ 让它在后台运行，不依赖命令窗口；

✅ 通过日志手动查看进度（例如实时写入 log.txt）；

✅ 即使关闭终端或断网也能继续执行（可选）；

✅ 方法一：使用 nohup + &（最推荐）
适用于 macOS / Linux / VPS 等：


```bash
nohup python3 domain_finder.py --letters --length 4 --limit 456976 --verify-api --threads 30 > finder.log 2>&1 &
```
含义	说明
nohup	保证即使你退出终端，程序继续运行
>	将标准输出重定向到 finder.log
2>&1	将错误输出也重定向到同一个文件
&	表示在后台运行

✅ 查看日志（实时）
```bash
tail -f finder.log
```
实时查看最新日志，Ctrl+C 退出查看（不会中断程序）

✅ 方法二：使用 screen 或 tmux 会话管理器（可选）

```bash
screen -S domain-check
# 进入 screen 后执行：
python3 domain_finder.py --letters --length 4 --limit 456976 --verify-api --threads 30
```
然后按下：

Ctrl+A 然后 D → 退出 screen，不中断任务

之后可恢复：

```bash
screen -r domain-check
```

✅ 方法三（Windows 专用）：使用 PowerShell 隐藏窗口（非 GUI）
若你在 Windows 环境：

可保存为 run_hidden.bat：
```bash
@echo off
start /min cmd /c python domain_finder.py --letters --length 4 --limit 456976 --verify-api --threads 30 > finder.log 2>&1

start /min：最小化窗口

> finder.log 2>&1：将所有输出重定向到日志文件
```

✅ 日志建议配置（Python 内部）
确保你在 domain_finder.py 中有如下记录机制：

```bash
import logging

logging.basicConfig(
    filename='finder.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("开始执行任务")
```



### 故障排除

#### Apple Silicon兼容性问题

M系列芯片有时会遇到兼容性问题。如果出现以下错误：

```
macOS 14 (1407) or later required, have instead 14 (1406) !
```

解决方法：
1. 使用我们的内置环境修补：
   ```bash
   python3 env_patch.py
   ```
   
2. 然后使用修补后的启动脚本：
   ```bash
   ./run_app.sh
   ```

### 贡献

我们欢迎社区贡献！如果您想参与贡献，请查看[贡献指南](CONTRIBUTING.md)。

### 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

---

## English Documentation

### Features

- 🚀 **High Performance Concurrent Checking** - Utilize multi-threading to check large numbers of domains quickly
- 🔍 **Multiple Query Types** - Support for letter, number, or mixed combination domain queries
- 🧰 **Multiple Interfaces** - GUI and command-line interfaces available
- 🔄 **Smart Resume Capability** - Support for interrupted large-scale scans
- 🌐 **API Verification Integration** - Support for multiple domain registrar API verifications
- 🍎 **Apple Silicon Optimized** - Performance optimized for M-series chips

### Installation

#### Requirements

- Python 3.8 or higher
- macOS Monterey(12.0) or higher (for GUI interface)
- Supports both Apple Silicon chips (M1/M2/M3) and Intel chips

#### Install from Source

```bash
# Clone the repository
git clone https://github.com/jnMetaCode/domain-finder.git
cd domain-finder

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.json.example config.json
# Edit config.json to add your API keys and settings
```

### Quick Start

1. Launch the application:

```bash
./run_app.sh
```

This script will automatically select the most suitable interface for your system.

2. Select language (optional):

```bash
./run_app.sh --lang=zh  # Chinese interface
./run_app.sh --lang=en  # English interface
```

### Interface Options

#### Simplified GUI

The simplified GUI provides an intuitive graphical environment, suitable for users unfamiliar with command line:

- **Domain Length**: Set the length of domains to check
- **Domain Type**: Choose letters, digits, or mixed type
- **Check Limit**: Set the maximum number of domains to check
- **Threads**: Adjust concurrent checking threads
- **API Verification**: Enable API verification of domain availability

#### Command Line Interface

The command line interface provides more customization options, suitable for advanced users:

```bash
python3 domain_finder.py --letters --length 4 --limit 100
```

Common parameters:
- `--letters`: Use letter combinations
- `--digits`: Use digit combinations
- `--alphanumeric`: Use alphanumeric combinations
- `--length N`: Set domain length
- `--limit N`: Limit number of checks
- `--threads N`: Set thread count
- `--verify-api`: Use API verification
- `--only-verify-api`: Only perform API verification
- `--verbose`: Show detailed output

### Full Scan Tool

For users who need to check all possible four-letter domains, we provide a dedicated full scan tool `run_full_scan.py`:

```bash
# Complete scan of all 4-letter domains
nohup python3 run_full_scan.py --final-verify > logs/full_scan.log 2>&1 &

# Scan with both DNS and API verification simultaneously
nohup python3 run_full_scan.py --verify-api --threads 50 > logs/full_scan.log 2>&1 &

# Scan domains with a specific prefix
python3 run_full_scan.py --prefix "a" --limit 10000 --verify-api
```

### Troubleshooting

#### Apple Silicon Compatibility Issues

M-series chips may sometimes encounter compatibility issues. If you see the following error:

```
macOS 14 (1407) or later required, have instead 14 (1406) !
```

Solution:
1. Use our built-in environment patch:
   ```bash
   python3 env_patch.py
   ```
   
2. Then use the patched startup script:
   ```bash
   ./run_app.sh
   ```

### Contributing

We welcome community contributions! If you want to contribute, please check out our [Contributing Guidelines](CONTRIBUTING.md).

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 作者 / Author

Alan

## 版本信息 / Version Information

版本 / Version: 1.1.0
更新日期 / Last Updated: 2025-03-30
