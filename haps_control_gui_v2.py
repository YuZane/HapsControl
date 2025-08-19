import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import os
import time
import threading
import configparser
from pathlib import Path

class HAPSControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HAPS控制工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 配置文件路径
        self.config_file = "haps_config.ini"
        
        # 加载或创建配置文件
        self.config = self.load_or_create_config()
        
        # 创建界面
        self.create_widgets()
        
    def load_or_create_config(self):
        """加载现有配置文件或创建新的默认配置文件"""
        config = configparser.ConfigParser()
        
        # 如果配置文件存在，加载它
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            return config
        
        # 创建默认配置
        config['Connection'] = {
            'plink_path': r"D:\tools\plink.exe",
            'confpro_path': r"C:\Synopsys\protocomp-rtQ-2020.03\bin64\mbin\confpro.exe",
            'host': "10.126.8.230",
            'user': "dell",
            'password': "Bsp@123",
            'bitfile_info_path': r"D:\tools\bitfile.info"
        }
        
        config['ResetCommands'] = {
            'haps': 'emu:8 cfg_reset_pulse FB1_A',
            'haps_master': 'emu:8 cfg_reset_pulse FB1_D',
            'haps_slave': 'emu:8 cfg_reset_pulse FB1_B'  # 默认值，可在配置文件中修改
        }
        
        config['BitFilePaths'] = {
            'path1': r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0212\prj\designs\project.conf",
            'path2': r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0219\prj\designs\project.conf",
            'path3': r"D:\zxl\mc20l\rtl0p8\mc20l_fpga_tag0301_va_2f_rmii_0307\prj\designs\project.conf",
            'default_index': '3'  # 默认使用第3个路径
        }
        
        # 保存默认配置
        with open(self.config_file, 'w') as f:
            config.write(f)
            
        return config
    
    def save_config(self):
        """保存配置到文件"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
        self.log(f"配置已保存到 {self.config_file}")
    
    def get_config_value(self, section, key, default=None):
        """获取配置值，带默认值"""
        try:
            return self.config[section][key]
        except:
            return default
    
    def create_widgets(self):
        # 配置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        self.style.configure("Header.TLabel", font=("微软雅黑", 12, "bold"))
        self.style.configure("SubHeader.TLabel", font=("微软雅黑", 10, "bold"))
        
        # 创建主框架
        main_notebook = ttk.Notebook(self.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 主操作标签页
        main_frame = ttk.Frame(main_notebook, padding="10")
        main_notebook.add(main_frame, text="操作")
        
        # 配置标签页
        config_frame = ttk.Frame(main_notebook, padding="10")
        main_notebook.add(config_frame, text="配置")
        
        # ================ 主操作界面 ================
        # 标题
        ttk.Label(main_frame, text="HAPS控制工具", style="Header.TLabel").pack(pady=(0, 20))
        
        # 功能选择框架 - 重置操作
        reset_frame = ttk.LabelFrame(main_frame, text="重置操作", padding="10")
        reset_frame.pack(fill=tk.X, pady=(0, 15))
        
        reset_buttons_frame = ttk.Frame(reset_frame)
        reset_buttons_frame.pack(pady=10)
        
        ttk.Button(reset_buttons_frame, text="重置HAPS", 
                  command=lambda: self.start_reset('haps')).pack(side=tk.LEFT, padx=10)
        ttk.Button(reset_buttons_frame, text="重置HAPS Master", 
                  command=lambda: self.start_reset('haps_master')).pack(side=tk.LEFT, padx=10)
        ttk.Button(reset_buttons_frame, text="重置HAPS Slave", 
                  command=lambda: self.start_reset('haps_slave')).pack(side=tk.LEFT, padx=10)
        
        # 加载配置框架
        self.load_frame = ttk.LabelFrame(main_frame, text="BitFile配置", padding="10")
        self.load_frame.pack(fill=tk.X, pady=(0, 15), expand=False)
        
        # BitFile路径选择
        path_frame = ttk.Frame(self.load_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="BitFile路径:").pack(side=tk.LEFT, padx=5)
        
        default_path_index = int(self.get_config_value('BitFilePaths', 'default_index', 3))
        default_path = self.get_config_value('BitFilePaths', f'path{default_path_index}', '')
        
        self.bitfile_path_var = tk.StringVar(value=default_path)
        self.bitfile_path_entry = ttk.Entry(path_frame, textvariable=self.bitfile_path_var, width=60)
        self.bitfile_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, text="浏览", command=self.browse_bitfile).pack(side=tk.LEFT, padx=5)
        
        # 预设路径选择
        ttk.Label(self.load_frame, text="预设路径:").pack(anchor=tk.W, pady=(10, 5))
        
        preset_frame = ttk.Frame(self.load_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        # 从配置文件加载预设路径
        self.preset_path_vars = []
        for i in range(1, 4):  # 支持3个预设路径
            path = self.get_config_value('BitFilePaths', f'path{i}', '')
            var = tk.StringVar(value=path)
            self.preset_path_vars.append(var)
            
            btn_frame = ttk.Frame(preset_frame)
            btn_frame.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            ttk.Label(btn_frame, text=f"路径 {i}:").pack(anchor=tk.W)
            ttk.Entry(btn_frame, textvariable=var).pack(fill=tk.X, pady=2)
            ttk.Button(btn_frame, text="使用", 
                      command=lambda v=var: self.bitfile_path_var.set(v.get())).pack(fill=tk.X)
        
        # 保存预设路径按钮
        ttk.Button(self.load_frame, text="保存预设路径", 
                  command=self.save_preset_paths).pack(pady=10)
        
        # 加载按钮
        ttk.Button(self.load_frame, text="执行加载", command=self.start_load).pack(pady=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(5, 0))
        
        # ================ 配置界面 ================
        # 连接配置
        conn_frame = ttk.LabelFrame(config_frame, text="连接配置", padding="10")
        conn_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.create_config_entry(conn_frame, "PLINK路径:", "Connection", "plink_path", 0)
        self.create_config_entry(conn_frame, "ConfPro路径:", "Connection", "confpro_path", 1)
        self.create_config_entry(conn_frame, "主机地址:", "Connection", "host", 2)
        self.create_config_entry(conn_frame, "用户名:", "Connection", "user", 3)
        self.create_config_entry(conn_frame, "密码:", "Connection", "password", 4, show="*")
        self.create_config_entry(conn_frame, "BitFile信息路径:", "Connection", "bitfile_info_path", 5)
        
        # 重置命令配置
        reset_cmd_frame = ttk.LabelFrame(config_frame, text="重置命令配置", padding="10")
        reset_cmd_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.create_config_entry(reset_cmd_frame, "重置HAPS命令:", "ResetCommands", "haps", 0)
        self.create_config_entry(reset_cmd_frame, "重置HAPS Master命令:", "ResetCommands", "haps_master", 1)
        self.create_config_entry(reset_cmd_frame, "重置HAPS Slave命令:", "ResetCommands", "haps_slave", 2)
        
        # 保存配置按钮
        ttk.Button(config_frame, text="保存配置", command=self.save_all_config).pack(pady=10)
        
        # 配置说明
        ttk.Label(config_frame, text="配置说明:", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(15, 5))
        config_help = "1. 所有配置将保存在程序目录下的haps_config.ini文件中\n" \
                      "2. 修改配置后需要点击保存配置按钮\n" \
                      "3. 重置命令格式: emu:8 cfg_reset_pulse [目标]\n" \
                      "4. 预设路径可在主界面修改和保存"
        ttk.Label(config_frame, text=config_help, justify=tk.LEFT).pack(anchor=tk.W)
        
        self.log("程序启动成功，配置已加载")
    
    def create_config_entry(self, parent, label_text, section, key, row, show=""):
        """创建配置项输入框"""
        ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky=tk.W, pady=5, padx=5)
        var = tk.StringVar(value=self.get_config_value(section, key, ""))
        # 存储变量引用，避免被垃圾回收
        if not hasattr(self, 'config_vars'):
            self.config_vars = {}
        self.config_vars[f"{section}.{key}"] = (var, section, key)
        
        entry = ttk.Entry(parent, textvariable=var, width=60, show=show)
        entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=5)
        return var
    
    def save_all_config(self):
        """保存所有配置项"""
        if hasattr(self, 'config_vars'):
            for key, (var, section, config_key) in self.config_vars.items():
                if section not in self.config:
                    self.config[section] = {}
                self.config[section][config_key] = var.get()
        
        self.save_config()
        messagebox.showinfo("保存成功", "配置已成功保存，部分配置需要重启程序才能生效")
    
    def browse_bitfile(self):
        filename = filedialog.askopenfilename(
            title="选择BitFile",
            filetypes=[("配置文件", "*.conf"), ("所有文件", "*.*")]
        )
        if filename:
            self.bitfile_path_var.set(filename)
    
    def save_preset_paths(self):
        """保存预设路径到配置文件"""
        for i, var in enumerate(self.preset_path_vars, 1):
            self.config['BitFilePaths'][f'path{i}'] = var.get()
        
        self.save_config()
        self.log("预设路径已保存")
        messagebox.showinfo("保存成功", "预设路径已成功保存")
    
    def log(self, message):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def set_status(self, status):
        """更新状态标签"""
        self.status_var.set(status)
        self.log(status)
    
    def test_connection(self):
        """测试与远程主机的连接"""
        plink_path = self.get_config_value('Connection', 'plink_path')
        host = self.get_config_value('Connection', 'host')
        user = self.get_config_value('Connection', 'user')
        password = self.get_config_value('Connection', 'password')
        
        self.set_status(f"正在连接到 {host}...")
        
        if not os.path.exists(plink_path):
            self.set_status(f"错误: PLINK路径不存在 - {plink_path}")
            return False
        
        try:
            # 构建plink命令测试连接
            command = [
                plink_path,
                "-ssh", f"{user}@{host}",
                "-pw", password,
                "exit"
            ]
            
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.set_status(f"成功连接到 {host}")
                return True
            else:
                self.set_status(f"连接失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.set_status(f"连接错误: {str(e)}")
            return False
    
    def execute_remote_command(self, command):
        """执行远程命令"""
        plink_path = self.get_config_value('Connection', 'plink_path')
        host = self.get_config_value('Connection', 'host')
        user = self.get_config_value('Connection', 'user')
        password = self.get_config_value('Connection', 'password')
        
        self.set_status(f"正在执行命令: {command}")
        
        if not os.path.exists(plink_path):
            self.set_status(f"错误: PLINK路径不存在 - {plink_path}")
            return False
        
        try:
            # 构建完整的plink命令
            full_command = [
                plink_path,
                "-ssh", f"{user}@{host}",
                "-pw", password,
                "-batch",
                command
            ]
            
            # 执行命令
            process = subprocess.Popen(
                full_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 实时输出命令结果
            for line in process.stdout:
                self.log(line.strip())
            
            # 等待命令完成并获取返回码
            process.wait()
            
            if process.returncode == 0:
                self.set_status(f"命令执行成功: {command}")
                return True
            else:
                self.set_status(f"命令执行失败 (返回码: {process.returncode}): {command}")
                return False
                
        except Exception as e:
            self.set_status(f"命令执行错误: {str(e)}")
            return False
    
    def start_reset(self, reset_type):
        """开始重置操作（在新线程中执行）"""
        self.log(f"===== 开始{reset_type}重置操作 =====")
        threading.Thread(target=self.perform_reset, args=(reset_type,), daemon=True).start()
    
    def perform_reset(self, reset_type):
        """执行重置操作"""
        # 获取配置的命令
        reset_command = self.get_config_value('ResetCommands', reset_type)
        confpro_path = self.get_config_value('Connection', 'confpro_path')
        
        if not reset_command:
            self.set_status(f"错误: 未配置{reset_type}的重置命令")
            self.log(f"===== {reset_type}重置操作失败 =====")
            return
        
        # 构建完整命令
        full_command = f'"{confpro_path}" {reset_command}'
        
        # 测试连接
        if not self.test_connection():
            self.log(f"===== {reset_type}重置操作失败 =====")
            return
        
        # 执行重置命令
        success = self.execute_remote_command(full_command)
        
        # 完成
        if success:
            self.set_status(f"===== {reset_type}重置操作成功完成 =====")
        else:
            self.set_status(f"===== {reset_type}重置操作失败 =====")
        
        self.set_status("20秒后操作完成")
        time.sleep(20)
        self.set_status("就绪")
    
    def start_load(self):
        """开始加载操作（在新线程中执行）"""
        self.log("===== 开始加载BitFile操作 =====")
        threading.Thread(target=self.perform_load, daemon=True).start()
    
    def perform_load(self):
        """执行加载操作"""
        bitfile_path = self.bitfile_path_var.get()
        bitfile_info_path = self.get_config_value('Connection', 'bitfile_info_path')
        confpro_path = self.get_config_value('Connection', 'confpro_path')
        
        # 检查文件是否存在
        if not os.path.exists(bitfile_path):
            self.log(f"指定的文件不存在: {bitfile_path}")
            self.log("尝试使用默认路径...")
            default_path_index = int(self.get_config_value('BitFilePaths', 'default_index', 3))
            bitfile_path = self.get_config_value('BitFilePaths', f'path{default_path_index}', '')
            self.bitfile_path_var.set(bitfile_path)
            
            if not os.path.exists(bitfile_path):
                self.log("默认路径文件也不存在")
                self.log("===== 加载操作失败 =====")
                return
        
        # 保存路径到info文件
        try:
            # 确保目录存在
            Path(bitfile_info_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(bitfile_info_path, "w") as f:
                f.write(bitfile_path)
            self.log(f"BitFile路径已保存到 {bitfile_info_path}")
        except Exception as e:
            self.log(f"保存BitFile路径失败: {str(e)}")
        
        # 测试连接
        if not self.test_connection():
            self.log("===== 加载操作失败 =====")
            return
        
        # 执行加载命令
        load_command = f'"{confpro_path}" emu:8 cfg_project_configure "{bitfile_path}"'
        success = self.execute_remote_command(load_command)
        
        # 完成
        if success:
            self.set_status("===== 加载操作成功完成 =====")
        else:
            self.set_status("===== 加载操作失败 =====")
        
        self.set_status("20秒后操作完成")
        time.sleep(20)
        self.set_status("就绪")

if __name__ == "__main__":
    root = tk.Tk()
    app = HAPSControlGUI(root)
    root.mainloop()
