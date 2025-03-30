#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版域名查找工具图形界面 - 适用于所有macOS系统
"""

import os
import sys
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import signal

# 应用环境修补 - 必须在所有导入之前进行
try:
    # 直接导入环境修补模块
    from env_patch import disable_version_check
    # 确保版本检查被禁用
    disable_version_check()
    print("已应用环境修补")
except ImportError:
    print("警告: 无法导入环境修补模块，某些功能可能不可用")

# 跳过所有版本检查逻辑
os.environ['SYSTEM_VERSION_COMPAT'] = '1'

# 检查Python版本
if sys.version_info < (3, 8):
    print("错误: 需要Python 3.8或更高版本")
    sys.exit(1)

# 显示版本信息
print(f"当前macOS版本: {platform.mac_ver()[0]}")
print(f"系统环境: {platform.platform()}")

class SimpleDomainFinderGUI:
    """域名查找工具的简化GUI实现"""
    
    def __init__(self, root):
        """初始化GUI界面"""
        self.root = root
        self.root.title("域名查找工具 - 通用版")
        self.root.geometry("860x640")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # 设置样式
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 12), padding=5)
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TLabelframe", font=("Arial", 12, "bold"))
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项框架
        options_frame = ttk.LabelFrame(main_frame, text="域名检查设置", padding="10")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 域名参数
        param_frame = ttk.Frame(options_frame)
        param_frame.pack(fill=tk.X, pady=5)
        
        # 域名长度
        ttk.Label(param_frame, text="域名长度:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.length_var = tk.IntVar(value=4)
        ttk.Spinbox(param_frame, from_=1, to=10, width=5, textvariable=self.length_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 类型选择
        ttk.Label(param_frame, text="域名类型:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.domain_type = tk.StringVar(value="letters")
        ttk.Combobox(param_frame, textvariable=self.domain_type, values=["letters", "digits", "mixed"]).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 限制数量
        ttk.Label(param_frame, text="检查数量:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.limit_var = tk.IntVar(value=100)
        ttk.Spinbox(param_frame, from_=1, to=1000, width=5, textvariable=self.limit_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 线程数
        ttk.Label(param_frame, text="线程数:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.threads_var = tk.IntVar(value=20)
        ttk.Spinbox(param_frame, from_=1, to=50, width=5, textvariable=self.threads_var).grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)
        
        # API验证选项
        self.use_api = tk.BooleanVar(value=False)
        ttk.Checkbutton(param_frame, text="使用API验证", variable=self.use_api).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # 按钮框架
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="开始检查", command=self.start_check).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="仅API验证", command=self.api_verify_only).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="查看结果", command=self.view_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="打开CLI", command=self.open_cli).pack(side=tk.RIGHT, padx=5)
        
        # 日志框架
        log_frame = ttk.LabelFrame(main_frame, text="检查日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态栏
        status_frame = ttk.Frame(root, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, anchor=tk.W).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        # 变量初始化
        self.process = None
        self.log_thread = None
        self.running = False
        
        # 更新日志
        self.add_log('域名查找工具已启动，请设置参数并点击"开始检查"')
        self.add_log(f"系统信息: {platform.system()} {platform.release()} ({platform.machine()})")
        self.add_log(f"macOS版本: {platform.mac_ver()[0]} (环境修补已应用)")
        
        # 检查必要文件
        self._check_files()
    
    def _check_files(self):
        """检查必要文件是否存在"""
        required_files = ['domain_finder.py']
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            self.add_log(f"警告: 找不到以下文件: {', '.join(missing_files)}")
            messagebox.showwarning("文件缺失", f"找不到以下文件:\n{', '.join(missing_files)}\n\n程序可能无法正常运行。")
    
    def add_log(self, message, error=False):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        if error:
            # 找到最后一行的开始和结束位置
            last_line_start = self.log_text.index("end-1c linestart")
            last_line_end = self.log_text.index("end-1c")
            self.log_text.tag_add("error", last_line_start, last_line_end)
            self.log_text.tag_config("error", foreground="red")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 更新状态栏
        self.status_var.set(message)
    
    def build_command(self, api_only=False):
        """构建命令行参数"""
        cmd = []
        
        if api_only:
            cmd.append("--only-verify-api")
            cmd.append("--limit")
            cmd.append(str(min(10, self.limit_var.get())))
        else:
            # 域名长度
            cmd.append("--length")
            cmd.append(str(self.length_var.get()))
            
            # 域名类型
            domain_type = self.domain_type.get()
            if domain_type == "letters":
                cmd.append("--letters")
            elif domain_type == "digits":
                cmd.append("--digits")
            elif domain_type == "mixed":
                cmd.append("--alphanumeric")
            
            # 检查数量
            cmd.append("--limit")
            cmd.append(str(self.limit_var.get()))
            
            # 线程数
            cmd.append("--threads")
            cmd.append(str(self.threads_var.get()))
            
            # API验证
            if self.use_api.get():
                cmd.append("--verify-api")
        
        # 添加详细输出
        cmd.append("--verbose")
        
        return cmd
    
    def start_check(self):
        """开始域名检查"""
        if self.running:
            messagebox.showinfo("提示", "已有检查任务正在运行")
            return
        
        cmd = self.build_command()
        self._run_command(cmd, "开始执行域名检查")
    
    def api_verify_only(self):
        """仅执行API验证"""
        if self.running:
            messagebox.showinfo("提示", "已有检查任务正在运行")
            return
        
        cmd = self.build_command(api_only=True)
        self._run_command(cmd, "开始API验证")
    
    def _run_command(self, cmd, start_message):
        """运行命令并捕获输出"""
        self.running = True
        
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # 添加启动日志
        self.add_log(start_message)
        self.add_log(f"命令: python domain_finder.py {' '.join(cmd)}")
        
        try:
            # 启动进程
            self.process = subprocess.Popen(
                ["python", "domain_finder.py"] + cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 在线程中读取输出
            self.log_thread = threading.Thread(target=self._read_output)
            self.log_thread.daemon = True
            self.log_thread.start()
        except Exception as e:
            self.add_log(f"启动失败: {str(e)}", error=True)
            self.running = False
    
    def _read_output(self):
        """读取进程输出"""
        try:
            for line in iter(self.process.stdout.readline, ''):
                if line:
                    self.add_log(line.rstrip())
            
            self.process.stdout.close()
            self.process.wait()
            
            if self.process.returncode == 0:
                self.add_log("检查完成", error=False)
            else:
                self.add_log(f"检查异常退出，返回码: {self.process.returncode}", error=True)
        except Exception as e:
            self.add_log(f"读取输出出错: {str(e)}", error=True)
        finally:
            self.running = False
    
    def view_results(self):
        """查看检查结果"""
        if os.path.exists('available_domains.csv'):
            try:
                # 清空日志
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete(1.0, tk.END)
                self.log_text.config(state=tk.DISABLED)
                
                self.add_log("查看可用域名结果:")
                
                # 读取文件
                with open('available_domains.csv', 'r') as f:
                    lines = f.readlines()
                
                # 显示结果
                for line in lines:
                    self.add_log(line.strip())
                
                self.add_log(f"找到 {len(lines)} 个可能可用的域名")
            except Exception as e:
                self.add_log(f"读取结果出错: {str(e)}", error=True)
        else:
            self.add_log("未找到结果文件 available_domains.csv", error=True)
    
    def open_cli(self):
        """打开命令行界面"""
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.Popen(["python", "run_m2.py"])
                self.add_log("已启动命令行界面")
            else:
                subprocess.Popen(["start", "python", "run_m2.py"], shell=True)
                self.add_log("已启动命令行界面")
        except Exception as e:
            self.add_log(f"无法启动命令行界面: {str(e)}", error=True)
    
    def on_close(self):
        """关闭窗口处理"""
        if self.running:
            if messagebox.askyesno("确认退出", "检查任务正在运行，确定要退出吗？"):
                if self.process:
                    try:
                        self.process.terminate()
                    except:
                        pass
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """主函数"""
    try:
        # 设置更好的缩放
        if platform.system() == "Windows":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        elif platform.system() == "Darwin":  # macOS
            os.environ['TK_SILENCE_DEPRECATION'] = '1'  # 抑制macOS的tk警告
        
        # 创建主窗口
        root = tk.Tk()
        app = SimpleDomainFinderGUI(root)
        
        # 设置图标（如果存在）
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "icon.ico")
        if os.path.exists(icon_path) and platform.system() == "Windows":
            root.iconbitmap(icon_path)
        
        # 启动主循环
        root.mainloop()
        
        return 0
    except Exception as e:
        print(f"错误: {str(e)}")
        messagebox.showerror("启动错误", f"无法启动GUI: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 