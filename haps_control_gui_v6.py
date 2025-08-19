import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import os
import time
import configparser
from pathlib import Path
import paramiko  # 需要安装: pip install paramiko
from paramiko.ssh_exception import SSHException, AuthenticationException, NoValidConnectionsError

class HAPSControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HAPS控制工具")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 配置文件路径
        self.config_file = "haps_config.ini"
        
        # 初始化配置变量
        self.config = None
        
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
            # 检查并修复可能的配置缺失
            self.fix_config(config)
            return config
        
        # 创建默认配置
        config['Connection'] = {
            'confpro_path': r"C:\Synopsys\protocomp-rtQ-2020.03\bin64\mbin\confpro.exe",
            'host': "10.126.8.230",
            'port': "22",  # SSH默认端口
            'user': "dell",
            'password': "Bsp@123",
            'bitfile_info_path': r"D:\tools\bitfile.info"
        }
        
        # 配置重置命令，使用分号分隔多条命令
        config['ResetCommands'] = {
            # reset master的两条指令
            'haps_master': 'emu:8 cfg_reset_pulse FB1_A;emu:8 cfg_reset_pulse FB1_D',
            # reset slave的两条指令
            'haps_slave': 'emu:8 cfg_reset_pulse FB1_B;emu:8 cfg_reset_pulse FB1_C',
            # reset haps的四条指令
            'haps': 'emu:8 cfg_reset_pulse FB1_A;emu:8 cfg_reset_pulse FB1_D;emu:8 cfg_reset_pulse FB1_B;emu:8 cfg_reset_pulse FB1_C'
        }
        
        # 配置加载命令，支持多条命令，用分号分隔
        config['LoadCommands'] = {
            'default': 'emu:8 cfg_project_configure "{bitfile_path}"'
        }
        
        # 命令间的等待时间(秒)
        config['Timing'] = {
            'command_delay': '2'
        }
        
        config['BitFilePaths'] = {
            'path1': r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0212\prj\designs\project.conf",
            'path2': r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0219\prj\designs\project.conf",
            'path3': r"D:\zxl\mc20l\rtl0p8\mc20l_fpga_tag0301_va_2f_rmii_0307\prj\designs\project.conf",
            'default_index': '3'
        }
        
        # 保存默认配置
        with open(self.config_file, 'w') as f:
            config.write(f)
            
        return config
    
    def fix_config(self, config):
        """检查并修复配置文件中可能缺失的部分或无效值"""
        # 检查Timing部分和command_delay配置
        if 'Timing' not in config:
            config['Timing'] = {}
        
        timing_updated = False
        if 'command_delay' not in config['Timing'] or not config['Timing']['command_delay']:
            config['Timing']['command_delay'] = '2'
            timing_updated = True
        
        # 确保重置命令部分存在
        if 'ResetCommands' not in config:
            config['ResetCommands'] = {}
            
        # 设置默认重置命令（如果不存在）
        default_commands = {
            'haps_master': 'emu:8 cfg_reset_pulse FB1_A;emu:8 cfg_reset_pulse FB1_D',
            'haps_slave': 'emu:8 cfg_reset_pulse FB1_B;emu:8 cfg_reset_pulse FB1_C',
            'haps': 'emu:8 cfg_reset_pulse FB1_A;emu:8 cfg_reset_pulse FB1_D;emu:8 cfg_reset_pulse FB1_B;emu:8 cfg_reset_pulse FB1_C'
        }
        
        commands_updated = False
        for cmd_name, cmd_value in default_commands.items():
            if cmd_name not in config['ResetCommands'] or not config['ResetCommands'][cmd_name]:
                config['ResetCommands'][cmd_name] = cmd_value
                commands_updated = True
        
        # 确保加载命令部分存在
        if 'LoadCommands' not in config:
            config['LoadCommands'] = {}
            commands_updated = True
            
        # 设置默认加载命令（如果不存在）
        if 'default' not in config['LoadCommands'] or not config['LoadCommands']['default']:
            config['LoadCommands']['default'] = 'emu:8 cfg_project_configure "{bitfile_path}"'
            commands_updated = True
        
        # 只有在配置确实有更新且self.config已初始化时才保存
        if (timing_updated or commands_updated) and self.config is not None:
            # 将修复后的配置写回配置对象
            self.config = config
            self.save_config()
            self.log("配置修复：更新了缺失或无效的配置项")
        
        return config
    
    def get_int_config_value(self, section, key, default=0):
        """安全地获取整数类型的配置值"""
        try:
            value_str = self.get_config_value(section, key, str(default))
            return int(value_str.strip())
        except ValueError:
            self.log(f"警告：配置项 {section}.{key} 的值 '{value_str}' 不是有效的整数，使用默认值 {default}")
            return default
    
    def save_config(self):
        """保存配置到文件"""
        if self.config is None:
            self.log("警告：配置未初始化，无法保存")
            return
            
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
                  command=lambda: self.perform_reset('haps')).pack(side=tk.LEFT, padx=10)
        ttk.Button(reset_buttons_frame, text="重置HAPS Master", 
                  command=lambda: self.perform_reset('haps_master')).pack(side=tk.LEFT, padx=10)
        ttk.Button(reset_buttons_frame, text="重置HAPS Slave", 
                  command=lambda: self.perform_reset('haps_slave')).pack(side=tk.LEFT, padx=10)
        
        # 加载配置框架
        self.load_frame = ttk.LabelFrame(main_frame, text="BitFile配置", padding="10")
        self.load_frame.pack(fill=tk.X, pady=(0, 15), expand=False)
        
        # BitFile路径选择
        path_frame = ttk.Frame(self.load_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="BitFile路径:").pack(side=tk.LEFT, padx=5)
        
        default_path_index = self.get_int_config_value('BitFilePaths', 'default_index', 3)
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
        ttk.Button(self.load_frame, text="执行加载", command=self.perform_load).pack(pady=5)
        
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
        
        # 创建配置项使用frame包装，统一用pack布局
        conn_grid_frame = ttk.Frame(conn_frame)
        conn_grid_frame.pack(fill=tk.X)
        
        # 创建连接配置项
        self.create_config_entry(conn_grid_frame, "ConfPro路径:", "Connection", "confpro_path", 0)
        self.create_config_entry(conn_grid_frame, "主机地址(IP):", "Connection", "host", 1)
        self.create_config_entry(conn_grid_frame, "SSH端口:", "Connection", "port", 2)
        self.create_config_entry(conn_grid_frame, "用户名:", "Connection", "user", 3)
        self.create_config_entry(conn_grid_frame, "密码:", "Connection", "password", 4, show="")
        self.create_config_entry(conn_grid_frame, "BitFile信息路径:", "Connection", "bitfile_info_path", 5)
        
        # 时间配置
        timing_frame = ttk.LabelFrame(config_frame, text="时间配置", padding="10")
        timing_frame.pack(fill=tk.X, pady=(0, 15))
        
        timing_grid_frame = ttk.Frame(timing_frame)
        timing_grid_frame.pack(fill=tk.X)
        self.create_config_entry(timing_grid_frame, "命令间等待时间(秒):", "Timing", "command_delay", 0)
        
        # 重置命令配置
        reset_cmd_frame = ttk.LabelFrame(config_frame, text="重置命令配置", padding="10")
        reset_cmd_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 提示信息使用pack布局
        ttk.Label(reset_cmd_frame, text="提示: 多条命令用分号(;)分隔").pack(anchor=tk.W, pady=(0, 10))
        
        # 命令输入框使用单独的frame，用grid布局
        reset_grid_frame = ttk.Frame(reset_cmd_frame)
        reset_grid_frame.pack(fill=tk.X)
        
        # 创建重置命令配置项
        self.create_config_entry(reset_grid_frame, "重置HAPS命令:", "ResetCommands", "haps", 0)
        self.create_config_entry(reset_grid_frame, "重置HAPS Master命令:", "ResetCommands", "haps_master", 1)
        self.create_config_entry(reset_grid_frame, "重置HAPS Slave命令:", "ResetCommands", "haps_slave", 2)
        
        # 加载命令配置
        load_cmd_frame = ttk.LabelFrame(config_frame, text="加载命令配置", padding="10")
        load_cmd_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 提示信息使用pack布局
        ttk.Label(load_cmd_frame, text="提示: 多条命令用分号(;)分隔，{bitfile_path}会被替换为实际文件路径").pack(anchor=tk.W, pady=(0, 10))
        
        # 命令输入框使用单独的frame，用grid布局
        load_grid_frame = ttk.Frame(load_cmd_frame)
        load_grid_frame.pack(fill=tk.X)
        
        # 创建加载命令配置项
        self.create_config_entry(load_grid_frame, "加载命令:", "LoadCommands", "default", 0)
        
        # 保存配置按钮
        ttk.Button(config_frame, text="保存配置", command=self.save_all_config).pack(pady=10)
        
        # 配置说明
        ttk.Label(config_frame, text="配置说明:", style="SubHeader.TLabel").pack(anchor=tk.W, pady=(15, 5))
        config_help = "1. 所有配置将保存在程序目录下的haps_config.ini文件中\n" \
                      "2. 修改配置后需要点击保存配置按钮\n" \
                      "3. 可配置多条重置和加载命令，用分号(;)分隔\n" \
                      "4. 命令之间会根据配置的时间间隔自动等待\n" \
                      "5. 加载命令中可用{bitfile_path}作为文件路径的占位符\n" \
                      "6. 预设路径可在主界面修改和保存\n" \
                      "7. 程序使用paramiko库进行SSH连接"
        ttk.Label(config_frame, text=config_help, justify=tk.LEFT).pack(anchor=tk.W)
        
        self.log("程序启动成功，配置已加载")
        self.log("注意：首次使用请确保已安装paramiko库 (pip install paramiko)")
    
    def create_config_entry(self, parent, label_text, section, key, row, show=""):
        """创建配置项输入框，使用grid布局"""
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
        messagebox.showinfo("保存成功", "配置已成功保存")
    
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
        # 强制刷新界面，确保日志实时显示
        self.root.update_idletasks()
    
    def set_status(self, status):
        """更新状态标签"""
        self.status_var.set(status)
        self.log(status)
    
    def create_ssh_client(self):
        """创建SSH客户端连接"""
        host = self.get_config_value('Connection', 'host')
        port = self.get_int_config_value('Connection', 'port', 22)
        user = self.get_config_value('Connection', 'user')
        password = self.get_config_value('Connection', 'password')
        
        try:
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            # 自动添加未知主机密钥
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            # 连接到服务器
            ssh.connect(host, port, user, password, timeout=10)
            self.log(f"成功连接到 {host}:{port}")
            return ssh
        except AuthenticationException:
            self.log(f"连接失败: 认证失败，请检查用户名和密码")
        except NoValidConnectionsError:
            self.log(f"连接失败: 无法连接到 {host}:{port}")
        except SSHException as e:
            self.log(f"SSH错误: {str(e)}")
        except Exception as e:
            self.log(f"连接错误: {str(e)}")
        return None
    
    def execute_remote_command(self, command):
        """使用paramiko执行远程命令"""
        self.set_status(f"正在执行命令: {command}")
        
        # 创建SSH连接
        ssh = self.create_ssh_client()
        if not ssh:
            return False
        
        try:
            # 执行命令
            stdin, stdout, stderr = ssh.exec_command(command)
            
            # 实时读取输出
            for line in stdout:
                self.log(line.strip())
            
            # 读取错误输出
            error_output = stderr.read().decode().strip()
            if error_output:
                self.log(f"命令错误输出: {error_output}")
            
            # 等待命令完成并获取返回码
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    line = stdout.readline()
                    if line:
                        self.log(line.strip())
                time.sleep(0.5)
            
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.set_status(f"命令执行成功: {command}")
                return True
            else:
                self.set_status(f"命令执行失败 (返回码: {exit_status}): {command}")
                return False
                
        except SSHException as e:
            self.set_status(f"命令执行错误: {str(e)}")
            return False
        finally:
            # 确保连接关闭
            if ssh:
                ssh.close()
                self.log("SSH连接已关闭")
    
    def perform_reset(self, reset_type):
        """执行重置操作（串行执行，无线程）"""
        # 禁用所有按钮防止重复操作
        self.disable_buttons(True)
        
        try:
            self.log(f"===== 开始{reset_type}重置操作 =====")
            
            # 获取配置的命令和参数，使用安全的整数转换方法
            reset_commands = self.get_config_value('ResetCommands', reset_type, "")
            confpro_path = self.get_config_value('Connection', 'confpro_path')
            command_delay = self.get_int_config_value('Timing', 'command_delay', 2)
            
            if not reset_commands:
                self.set_status(f"错误: 未配置{reset_type}的重置命令")
                self.log(f"===== {reset_type}重置操作失败 =====")
                return
            
            # 分割多条命令
            commands = [cmd.strip() for cmd in reset_commands.split(';') if cmd.strip()]
            
            if not commands:
                self.set_status(f"错误: 未找到有效的{reset_type}重置命令")
                self.log(f"===== {reset_type}重置操作失败 =====")
                return
            
            # 逐条执行命令
            all_success = True
            for i, cmd in enumerate(commands, 1):
                self.log(f"\n===== 执行第 {i}/{len(commands)} 条命令 =====")
                
                # 构建完整命令 - 结合confpro路径和具体命令
                full_command = f'"{confpro_path}" {cmd}'
                
                # 执行命令
                success = self.execute_remote_command(full_command)
                if not success:
                    all_success = False
                    # 询问是否继续执行后续命令
                    if not self.ask_continue_on_error():
                        break
                
                # 如果不是最后一条命令，等待指定时间
                if i < len(commands) and command_delay > 0:
                    self.set_status(f"等待 {command_delay} 秒后执行下一条命令...")
                    for _ in range(command_delay):
                        time.sleep(1)
                        self.root.update_idletasks()  # 刷新界面
            
            # 完成
            if all_success:
                self.set_status(f"===== {reset_type}重置操作全部成功完成 =====")
            else:
                self.set_status(f"===== {reset_type}重置操作部分失败 =====")
            
            self.set_status("操作完成")
            
        finally:
            # 恢复按钮状态
            self.disable_buttons(False)
    
    def perform_load(self):
        """执行加载操作（支持多条命令）"""
        # 禁用所有按钮防止重复操作
        self.disable_buttons(True)
        
        try:
            self.log("===== 开始加载BitFile操作 =====")
            
            bitfile_path = self.bitfile_path_var.get()
            bitfile_info_path = self.get_config_value('Connection', 'bitfile_info_path')
            confpro_path = self.get_config_value('Connection', 'confpro_path')
            load_commands = self.get_config_value('LoadCommands', 'default', '')
            command_delay = self.get_int_config_value('Timing', 'command_delay', 2)
            
            # 检查文件是否存在
            if not os.path.exists(bitfile_path):
                self.log(f"指定的文件不存在: {bitfile_path}")
                self.log("尝试使用默认路径...")
                default_path_index = self.get_int_config_value('BitFilePaths', 'default_index', 3)
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
            
            # 检查加载命令配置
            if not load_commands:
                self.log("错误: 未配置加载命令")
                self.log("===== 加载操作失败 =====")
                return
                
            # 分割多条命令
            commands = [cmd.strip() for cmd in load_commands.split(';') if cmd.strip()]
            
            if not commands:
                self.log("错误: 未找到有效的加载命令")
                self.log("===== 加载操作失败 =====")
                return
            
            # 逐条执行命令
            all_success = True
            for i, cmd in enumerate(commands, 1):
                self.log(f"\n===== 执行第 {i}/{len(commands)} 条加载命令 =====")
                
                # 替换命令中的占位符为实际文件路径
                cmd_with_path = cmd.replace("{bitfile_path}", bitfile_path)
                
                # 构建完整命令 - 结合confpro路径和具体命令
                full_command = f'"{confpro_path}" {cmd_with_path}'
                
                # 执行命令
                success = self.execute_remote_command(full_command)
                if not success:
                    all_success = False
                    # 询问是否继续执行后续命令
                    if not self.ask_continue_on_error():
                        break
                
                # 如果不是最后一条命令，等待指定时间
                if i < len(commands) and command_delay > 0:
                    self.set_status(f"等待 {command_delay} 秒后执行下一条命令...")
                    for _ in range(command_delay):
                        time.sleep(1)
                        self.root.update_idletasks()  # 刷新界面
            
            # 完成
            if all_success:
                self.set_status("===== 加载操作全部成功完成 =====")
            else:
                self.set_status("===== 加载操作部分失败 =====")
                
            self.set_status("操作完成")
            
        finally:
            # 恢复按钮状态
            self.disable_buttons(False)
    
    def disable_buttons(self, disable):
        """启用/禁用所有操作按钮"""
        # 遍历所有按钮并设置状态
        for widget in self.root.winfo_children():
            self._disable_widget(widget, disable)
        # 刷新界面
        self.root.update_idletasks()
    
    def _disable_widget(self, widget, disable):
        """递归禁用/启用控件及其子控件"""
        if isinstance(widget, ttk.Button):
            widget.config(state=tk.DISABLED if disable else tk.NORMAL)
        # 处理包含子控件的容器
        for child in widget.winfo_children():
            self._disable_widget(child, disable)
    
    def ask_continue_on_error(self):
        """询问用户在命令执行错误时是否继续"""
        # 创建一个模态对话框
        result = messagebox.askyesno(
            "命令执行错误",
            "当前命令执行失败，是否继续执行后续命令？"
        )
        return result

if __name__ == "__main__":
    root = tk.Tk()
    app = HAPSControlGUI(root)
    root.mainloop()
