# 贡献指南 / Contributing Guidelines

[English](#contributing-guidelines-english) | [中文](#贡献指南-中文)

## 贡献指南 (中文)

感谢您对域名查找工具项目的关注！我们欢迎各种形式的贡献，包括错误报告、功能请求、文档改进和代码贡献。

### 如何贡献

#### 报告问题

如果您发现了bug或有功能请求，请在GitHub上[创建一个新的issue](https://github.com/jnMetaCode/domain-finder/issues/new)，并提供以下信息：

- 问题的详细描述
- 复现步骤（如果是bug）
- 您的操作系统和Python版本
- 如果是M系列芯片相关问题，请提供完整的macOS版本信息

#### 提交更改

1. 从主仓库Fork项目
2. 克隆您的Fork：`git clone https://github.com/your-username/domain-finder.git`
3. 创建分支：`git checkout -b feature/my-feature` 或 `git checkout -b fix/my-fix`
4. 进行修改并测试
5. 提交更改：`git commit -m "描述更改"`
6. 推送到您的Fork：`git push origin feature/my-feature`
7. 创建Pull Request到主仓库

### 代码风格

- 遵循PEP 8 Python代码风格指南
- 使用有意义的变量名和函数名
- 添加适当的注释，特别是对于复杂的逻辑
- 包含适当的文档字符串

### 测试

- 提交前请确保您的代码在各种环境中都能正常工作
- 对于M系列芯片相关的更改，请确保在Apple Silicon设备上测试
- 如果添加新功能，请考虑添加相应的测试

### 项目结构

```
domain-finder/
├── domain_finder.py           # 核心功能模块
├── run_app.sh                 # 启动脚本
├── run_full_scan.py           # 全面扫描工具
├── porkbun_api.py             # Porkbun API集成
├── dynadot_api.py             # Dynadot API集成
├── env_patch.py               # 环境修补工具
├── config.json.example        # 配置示例
├── requirements.txt           # 依赖项
├── README.md                  # 项目文档
├── CONTRIBUTING.md            # 贡献指南
├── LICENSE                    # MIT许可证
├── tests/                     # 测试目录
├── docs/                      # 文档目录
├── logs/                      # 日志目录
└── results/                   # 结果输出目录
```

### 开发环境设置

1. 创建虚拟环境：
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # 如果存在
   ```

## M系列芯片注意事项

针对Apple Silicon芯片的贡献，请注意：

1. 考虑LibreSSL和OpenSSL兼容性问题
2. 测试GUI在M系列芯片上的显示和性能
3. 使用`./test_m2_compat.py`验证兼容性

## API集成

添加新的域名注册商API时：

1. 在`config.json`中添加新的provider配置
2. 在`domain_finder.py`中实现相应的API调用函数
3. 添加错误处理和重试机制
4. 提供详细文档，包括API需要的密钥和配置

## 文档

- 请更新README.md以反映您的更改
- 对于新功能，添加使用示例
- 保持文档的中英文版本同步

## 许可证

通过贡献代码，您同意您的贡献将根据项目的MIT许可证进行许可。

---

## Contributing Guidelines (English)

Thank you for your interest in the Domain Finder project! We welcome all forms of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

### How to Contribute

#### Reporting Issues

If you find a bug or have a feature request, please [create a new issue](https://github.com/jnMetaCode/domain-finder/issues/new) on GitHub with the following information:

- Detailed description of the issue
- Steps to reproduce (if it's a bug)
- Your operating system and Python version
- For M-series chip related issues, please provide complete macOS version information

#### Submitting Changes

1. Fork the main repository
2. Clone your fork: `git clone https://github.com/your-username/domain-finder.git`
3. Create a branch: `git checkout -b feature/my-feature` or `git checkout -b fix/my-fix`
4. Make changes and test
5. Commit changes: `git commit -m "Description of changes"`
6. Push to your fork: `git push origin feature/my-feature`
7. Create a Pull Request to the main repository

### Code Style

- Follow PEP 8 Python code style guidelines
- Use meaningful variable and function names
- Add appropriate comments, especially for complex logic
- Include proper docstrings

### Testing

- Ensure your code works in various environments before submitting
- For M-series chip related changes, please test on Apple Silicon devices
- If adding new features, consider adding corresponding tests

### Project Structure

```
domain-finder/
├── domain_finder.py           # Core functionality module
├── run_app.sh                 # Startup script
├── run_full_scan.py           # Full scan tool
├── porkbun_api.py             # Porkbun API integration
├── dynadot_api.py             # Dynadot API integration
├── env_patch.py               # Environment patching tool
├── config.json.example        # Configuration example
├── requirements.txt           # Dependencies
├── README.md                  # Project documentation
├── CONTRIBUTING.md            # Contributing guidelines
├── LICENSE                    # MIT license
├── tests/                     # Test directory
├── docs/                      # Documentation directory
├── logs/                      # Log directory
└── results/                   # Results output directory
```

### Development Environment Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## License

By contributing code, you agree that your contributions will be licensed under the project's MIT License. 