import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import subprocess
import os
import time
import threading

class HAPSControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("HAPS控制工具")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 配置样式
        self.style = ttk.Style()
        self.style.configure("TButton", font=("微软雅黑", 10))
        self.style.configure("TLabel", font=("微软雅黑", 10))
        self.style.configure("Header.TLabel", font=("微软雅黑", 12, "bold"))
        
        # 配置参数
        self.plink_path = r"D:\tools\plink.exe"
        self.bitfile_info_path = r"D:\tools\bitfile.info"
        self.host = "10.126.8.230"
        self.user = "dell"
        self.password = "Bsp@123"
        self.confpro_path = r"C:\Synopsys\protocomp-rtQ-2020.03\bin64\mbin\confpro.exe"
        
        # 默认BitFile路径
        self.default_bitfile_paths = [
            r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0212\prj\designs\project.conf",
            r"D:\zxl\mc20l\mc20l_fpga_tag0121_va_rmii_2f_0219\prj\designs\project.conf",
            r"D:\zxl\mc20l\rtl0p8\mc20l_fpga_tag0301_va_2f_rmii_0307\prj\designs\project.conf"
        ]
        self.current_bitfile_path = self.default_bitfile_paths[-1]
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="HAPS控制工具", style="Header.TLabel").pack(pady=(0, 20))
        
        # 功能选择框架
        function_frame = ttk.LabelFrame(main_frame, text="功能选择", padding="10")
        function_frame.pack(fill=tk.X, pady=(0, 15))
        
        # 按钮
        button_frame = ttk.Frame(function_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="重置HAPS", command=self.start_reset).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="加载BitFile", command=self.show_load_frame).pack(side=tk.LEFT, padx=10)
        
        # 加载配置框架
        self.load_frame = ttk.LabelFrame(main_frame, text="BitFile配置", padding="10")
        self.load_frame.pack(fill=tk.X, pady=(0, 15), expand=False)
        
        # BitFile路径选择
        path_frame = ttk.Frame(self.load_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="BitFile路径:").pack(side=tk.LEFT, padx=5)
        
        self.bitfile_path_var = tk.StringVar(value=self.current_bitfile_path)
        self.bitfile_path_entry = ttk.Entry(path_frame, textvariable=self.bitfile_path_var, width=60)
        self.bitfile_path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, text="浏览", command=self.browse_bitfile).pack(side=tk.LEFT, padx=5)
        
        # 预设路径选择
        ttk.Label(self.load_frame, text="预设路径:").pack(anchor=tk.W, pady=(10, 5))
        
        preset_frame = ttk.Frame(self.load_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        
        for i, path in enumerate(self.default_bitfile_paths):
            btn = ttk.Button(
                preset_frame, 
                text=f"路径 {i+1}", 
                command=lambda p=path: self.bitfile_path_var.set(p)
            )
            btn.pack(side=tk.LEFT, padx=5)
        
        # 加载按钮
        ttk.Button(self.load_frame, text="执行加载", command=self.start_load).pack(pady=10)
        
        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.status_var).pack(anchor=tk.W, pady=(5, 0))
        
        # 默认隐藏加载框架
        self.load_frame.pack_forget()
    
    def browse_bitfile(self):
        filename = filedialog.askopenfilename(
            title="选择BitFile",
            filetypes=[("配置文件", "*.conf"), ("所有文件", "*.*")]
        )
        if filename:
            self.bitfile_path_var.set(filename)
    
    def show_load_frame(self):
        self.load_frame.pack(fill=tk.X, pady=(0, 15), expand=False)
        self.log("显示BitFile加载配置")
    
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
        self.set_status(f"正在连接到 {self.host}...")
        
        try:
            # 构建plink命令测试连接
            command = [
                self.plink_path,
                "-ssh", f"{self.user}@{self.host}",
                "-pw", self.password,
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
                self.set_status(f"成功连接到 {self.host}")
                return True
            else:
                self.set_status(f"连接失败: {result.stderr}")
                return False
                
        except Exception as e:
            self.set_status(f"连接错误: {str(e)}")
            return False
    
    def execute_remote_command(self, command):
        """执行远程命令"""
        self.set_status(f"正在执行命令: {command}")
        
        try:
            # 构建完整的plink命令
            full_command = [
                self.plink_path,
                "-ssh", f"{self.user}@{self.host}",
                "-pw", self.password,
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
    
    def start_reset(self):
        """开始重置操作（在新线程中执行）"""
        self.log("===== 开始重置操作 =====")
        threading.Thread(target=self.perform_reset, daemon=True).start()
    
    def perform_reset(self):
        """执行重置操作"""
        # 测试连接
        if not self.test_connection():
            self.log("===== 重置操作失败 =====")
            return
        
        # 执行第一个重置命令
        reset_command1 = f'"{self.confpro_path}" emu:8 cfg_reset_pulse FB1_A'
        success1 = self.execute_remote_command(reset_command1)
        
        # 等待2秒
        self.set_status("等待2秒...")
        time.sleep(2)
        
        # 执行第二个重置命令
        reset_command2 = f'"{self.confpro_path}" emu:8 cfg_reset_pulse FB1_D'
        success2 = self.execute_remote_command(reset_command2)
        
        # 完成
        if success1 and success2:
            self.set_status("===== 重置操作成功完成 =====")
        else:
            self.set_status("===== 重置操作部分失败 =====")
        
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
        
        # 检查文件是否存在
        if not os.path.exists(bitfile_path):
            self.log(f"指定的文件不存在: {bitfile_path}")
            self.log("使用默认路径...")
            bitfile_path = self.default_bitfile_paths[-1]
            self.bitfile_path_var.set(bitfile_path)
        
        # 保存路径到info文件
        try:
            with open(self.bitfile_info_path, "w") as f:
                f.write(bitfile_path)
            self.log(f"BitFile路径已保存到 {self.bitfile_info_path}")
        except Exception as e:
            self.log(f"保存BitFile路径失败: {str(e)}")
        
        # 测试连接
        if not self.test_connection():
            self.log("===== 加载操作失败 =====")
            return
        
        # 执行加载命令
        load_command = f'"{self.confpro_path}" emu:8 cfg_project_configure "{bitfile_path}"'
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
