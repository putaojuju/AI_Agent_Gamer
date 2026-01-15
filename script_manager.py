# -*- coding: utf-8 -*-
"""
游戏脚本管理器 - 可视化UI
用于控制脚本的运行和管理本地脚本
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import threading
import time
import queue
import psutil
import win32gui
import win32con
import win32api
import win32process
import logging
import logging.handlers

# 配置日志系统
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('script_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏脚本管理器")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 脚本列表
        self.scripts = []
        
        # 脚本运行状态
        self.running_scripts = {}
        self.log_queue = queue.Queue()
        
        # 资源监控标志
        self.resource_monitoring = True
        
        # 虚拟环境配置
        self.venv_python = self._get_venv_python()
        self.log(f"使用Python解释器: {self.venv_python}")
        
        # 创建UI
        self.create_widgets()
        
        # 加载脚本
        self.load_scripts()
        
        # 启动日志更新线程
        self.update_logs()
        
        # 启动资源监控
        self.start_resource_monitoring()
        
        # 检查环境状态
        self.check_environment()
    
    def monitor_resources(self):
        """监控系统资源占用"""
        self.log("启动资源监控")
        
        while self.resource_monitoring:
            time.sleep(10)  # 每10秒检测一次
            
            try:
                # 获取CPU使用率
                cpu_usage = psutil.cpu_percent(interval=1)
                # 获取内存使用率
                mem_usage = psutil.virtual_memory().percent
                # 获取磁盘使用率
                disk_usage = psutil.disk_usage('/').percent
                
                # 记录日志
                resource_info = f"系统资源 - CPU: {cpu_usage:.1f}%, 内存: {mem_usage:.1f}%, 磁盘: {disk_usage:.1f}%"
                self.log(resource_info)
                
                # 如果资源占用过高，发送警告
                if cpu_usage > 80 or mem_usage > 80:
                    warning_msg = f"警告: 资源占用过高 - {resource_info}"
                    self.log(warning_msg)
                    messagebox.showwarning("资源警告", warning_msg)
                    
            except Exception as e:
                self.log(f"资源监控错误：{str(e)}")
                time.sleep(5)  # 错误后暂停5秒再继续监控
    
    def start_resource_monitoring(self):
        """启动资源监控线程"""
        self.resource_monitoring = True
        resource_thread = threading.Thread(target=self.monitor_resources, daemon=True)
        resource_thread.start()
        self.log("资源监控线程已启动")
    
    def stop_resource_monitoring(self):
        """停止资源监控"""
        self.resource_monitoring = False
        self.log("资源监控已停止")
    
    def _get_venv_python(self):
        """获取虚拟环境Python解释器路径"""
        # 项目根目录
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # 虚拟环境Python解释器路径
        venv_python = os.path.join(project_root, "venv", "Scripts", "python.exe")
        
        # 检查虚拟环境是否存在
        if os.path.exists(venv_python):
            self.log(f"检测到虚拟环境: {venv_python}")
            return venv_python
        
        # 如果是PyInstaller打包环境
        if getattr(sys, 'frozen', False):
            # 打包环境下使用当前解释器
            self.log("PyInstaller打包环境，使用当前Python解释器")
            return sys.executable
        
        # 否则使用当前解释器
        self.log("未检测到虚拟环境，使用当前Python解释器")
        return sys.executable
    
    def check_environment(self):
        """检查环境状态"""
        self.log("开始检查环境状态...")
        
        # 检查Python版本
        python_version = sys.version.split()[0]
        self.log(f"Python版本: {python_version}")
        
        # 检查虚拟环境Python版本
        try:
            venv_version = subprocess.check_output([self.venv_python, '--version'], 
                                                 text=True).strip()
            self.log(f"虚拟环境Python版本: {venv_version}")
        except Exception as e:
            self.log(f"获取虚拟环境版本失败: {str(e)}")
        
        # 检查关键依赖（使用虚拟环境Python解释器）
        dependencies = ["numpy", "airtest", "psutil", "win32gui", "cv2"]
        
        # 直接使用虚拟环境Python解释器检查依赖，不依赖当前环境
        self.log("使用虚拟环境Python解释器检查依赖...")
        
        # 构建检查命令，使用单引号避免转义问题
        check_cmd = [
            self.venv_python,
            '-c',
            '''
import sys

deps = ['numpy', 'airtest', 'psutil', 'win32gui', 'cv2']
results = []
for dep in deps:
    try:
        __import__(dep)
        results.append((dep, True, None))
    except ImportError as e:
        results.append((dep, False, str(e)))
print(results)
'''        ]
        
        try:
            result = subprocess.check_output(check_cmd, text=True, 
                                           stderr=subprocess.STDOUT)
            
            # 解析结果
            import ast
            results = ast.literal_eval(result.strip())
            
            all_venv_installed = True
            for dep, installed, error in results:
                if installed:
                    self.log(f"✓ 虚拟环境中依赖 {dep} 已安装")
                else:
                    self.log(f"✗ 虚拟环境中依赖 {dep} 未安装: {error}")
                    all_venv_installed = False
            
            if not all_venv_installed:
                self.log("警告：虚拟环境依赖不完整")
                # 不再弹出错误对话框，仅记录日志
                # messagebox.showerror("环境错误", "虚拟环境依赖不完整，请运行 venv\Scripts\pip install -r requirements.txt")
            
        except Exception as e:
            self.log(f"使用虚拟环境检查依赖失败: {str(e)}")
            # 如果检查失败，不再报错，继续运行
            self.log("依赖检查失败，继续运行...")
        
        self.log("环境检查完成")
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题
        title_label = ttk.Label(main_frame, text="游戏脚本管理器", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=10)
        
        # 日志显示状态
        self.log_visible = tk.BooleanVar(value=True)
        
        # 创建可调整大小的分栏布局
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # ==================== 左侧功能区域 ====================#
        left_frame = ttk.Frame(self.paned_window, padding="10")
        
        # 创建带滚动条的容器
        scrollable_frame = ttk.Frame(left_frame)
        scrollable_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Canvas和滚动条
        canvas = tk.Canvas(scrollable_frame)
        scrollbar = ttk.Scrollbar(scrollable_frame, orient="vertical", command=canvas.yview)
        scrollable_inner_frame = ttk.Frame(canvas)
        
        # 绑定滚动事件
        scrollable_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        # 创建Canvas窗口
        canvas.create_window((0, 0), window=scrollable_inner_frame, anchor="nw")
        
        # 配置Canvas和滚动条
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 添加鼠标滚轮支持
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # ==================== 左侧功能区域内容 ====================#
        # 脚本列表框架
        script_list_frame = ttk.LabelFrame(scrollable_inner_frame, text="脚本列表", padding="10")
        script_list_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # 脚本列表Treeview
        self.script_tree = ttk.Treeview(script_list_frame, columns=("name", "path", "status"), show="headings")
        self.script_tree.heading("name", text="脚本名称")
        self.script_tree.heading("path", text="脚本路径")
        self.script_tree.heading("status", text="状态")
        self.script_tree.column("name", width=150, minwidth=100)
        self.script_tree.column("path", width=300, minwidth=200)
        self.script_tree.column("status", width=80, minwidth=60)
        
        # 脚本列表滚动条
        script_scrollbar = ttk.Scrollbar(script_list_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscroll=script_scrollbar.set)
        
        # 布局脚本列表
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        script_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 脚本操作按钮区域 - 移动到脚本列表下方，确保可见
        button_frame = ttk.LabelFrame(scrollable_inner_frame, text="脚本操作", padding="10")
        button_frame.pack(fill=tk.X, pady=(0, 10), expand=False)
        
        # 增加按钮间距和大小，使其更醒目
        button_style = ttk.Style()
        button_style.configure("ScriptButton.TButton", font=("微软雅黑", 10, "bold"), padding=10)
        
        # 使用pack布局，确保按钮始终可见
        ttk.Button(button_frame, text="运行脚本", command=self.run_script, style="ScriptButton.TButton").pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="停止脚本", command=self.stop_script, style="ScriptButton.TButton").pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_scripts, style="ScriptButton.TButton").pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(button_frame, text="添加脚本", command=self.add_script, style="ScriptButton.TButton").pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # 运行模式选择
        mode_frame = ttk.LabelFrame(scrollable_inner_frame, text="运行模式", padding="5")
        mode_frame.pack(fill=tk.X, pady=(0, 10), expand=False)
        
        self.run_mode = tk.StringVar(value="normal")
        ttk.Radiobutton(mode_frame, text="正常模式", variable=self.run_mode, value="normal").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="后台模式", variable=self.run_mode, value="background").pack(side=tk.LEFT, padx=10)
        
        # 后台运行方式选择
        bg_mode_frame = ttk.Frame(mode_frame)
        bg_mode_frame.pack(fill=tk.X, pady=(5, 0), expand=False)
        
        ttk.Label(bg_mode_frame, text="后台运行方式:", width=12).pack(side=tk.LEFT, padx=10)
        
        self.bg_run_mode = tk.StringVar(value="message")
        bg_mode_options = {
            "消息模式": "message",      # 基于窗口消息，不影响前台
            "透明模式": "transparent",  # 窗口透明+屏幕外
            "最小化模式": "minimize",    # 窗口最小化
            "隐藏模式": "hide"          # 窗口完全隐藏
        }
        
        bg_mode_combo = ttk.Combobox(bg_mode_frame, textvariable=self.bg_run_mode, values=list(bg_mode_options.keys()))
        bg_mode_combo.pack(side=tk.LEFT, padx=5)
        
        # 后台模式说明
        ttk.Label(bg_mode_frame, text="消息模式：不影响前台操作，真正后台运行", font=("微软雅黑", 8)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, anchor=tk.W)
        
        # 游戏信息输入
        game_info_frame = ttk.LabelFrame(scrollable_inner_frame, text="游戏信息", padding="10")
        game_info_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        # 窗口选择按钮 - 后台模式添加游戏的关键按钮
        window_select_frame = ttk.Frame(game_info_frame)
        window_select_frame.pack(fill=tk.X, pady=(5, 5), expand=False)
        ttk.Label(window_select_frame, text="窗口选择:", width=8).pack(side=tk.LEFT, anchor=tk.NW)
        ttk.Button(window_select_frame, text="选择游戏窗口", command=self.select_game_window, width=15).pack(side=tk.LEFT, padx=(5, 5), pady=2)
        self.window_hint_label = ttk.Label(window_select_frame, text="点击按钮后，移动鼠标到游戏窗口上并按下Alt键选择", font=("微软雅黑", 8))
        self.window_hint_label.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor=tk.NW, pady=2)
        
        # 游戏路径 - 独立一行，确保可见
        game_path_frame = ttk.Frame(game_info_frame)
        game_path_frame.pack(fill=tk.X, pady=(5, 5), expand=False)
        ttk.Label(game_path_frame, text="游戏路径:", width=8).pack(side=tk.LEFT, anchor=tk.NW, pady=2)
        self.game_path_entry = ttk.Entry(game_path_frame, width=30)
        self.game_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5), pady=2)
        ttk.Button(game_path_frame, text="浏览", command=self.browse_game_path, width=8).pack(side=tk.LEFT, pady=2)
        
        # 游戏标题 - 独立一行，确保可见
        game_title_frame = ttk.Frame(game_info_frame)
        game_title_frame.pack(fill=tk.X, pady=(5, 5), expand=False)
        ttk.Label(game_title_frame, text="游戏标题:", width=8).pack(side=tk.LEFT, anchor=tk.NW, pady=2)
        self.game_title_entry = ttk.Entry(game_title_frame, width=40)
        self.game_title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5), pady=2)
        
        # ==================== 右侧区域 ====================#
        self.right_frame = ttk.Frame(self.paned_window, padding="10")
        
        # 添加标签页控件，支持日志和游戏嵌入视图切换
        self.right_notebook = ttk.Notebook(self.right_frame)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)
        
        # ------------------ 日志标签页 ------------------#
        log_tab = ttk.Frame(self.right_notebook)
        self.right_notebook.add(log_tab, text="运行日志")
        
        # 日志标题和控制栏
        log_header_frame = ttk.Frame(log_tab)
        log_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        log_title_label = ttk.Label(log_header_frame, text="运行日志", font=("微软雅黑", 10, "bold"))
        log_title_label.pack(side=tk.LEFT)
        
        # 日志显示/隐藏切换按钮
        ttk.Checkbutton(log_header_frame, text="显示日志", variable=self.log_visible, 
                       command=self.toggle_log_visibility, style="Toggle.TCheckbutton").pack(side=tk.RIGHT)
        
        # 日志内容框架
        self.log_content_frame = ttk.Frame(log_tab)
        self.log_content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 日志文本框
        self.log_text = tk.Text(self.log_content_frame, wrap=tk.WORD, state=tk.DISABLED, font=("Courier New", 10))
        
        # 日志滚动条
        log_scrollbar = ttk.Scrollbar(self.log_content_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=log_scrollbar.set)
        
        # 布局日志区域
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # ------------------ 游戏嵌入标签页 ------------------#
        game_tab = ttk.Frame(self.right_notebook)
        self.right_notebook.add(game_tab, text="游戏嵌入")
        
        # 游戏嵌入控制栏
        game_control_frame = ttk.Frame(game_tab)
        game_control_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(game_control_frame, text="游戏嵌入", font=("微软雅黑", 10, "bold")).pack(side=tk.LEFT)
        
        # 嵌入控制按钮
        embed_buttons_frame = ttk.Frame(game_control_frame)
        embed_buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(embed_buttons_frame, text="嵌入游戏窗口", command=self.embed_game_window, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(embed_buttons_frame, text="取消嵌入", command=self.unembed_game_window, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(embed_buttons_frame, text="选择游戏", command=self.select_game_window, width=12).pack(side=tk.LEFT, padx=5)
        
        # 游戏窗口嵌入区域
        self.embed_frame = ttk.Frame(game_tab, relief=tk.SUNKEN, borderwidth=1)
        self.embed_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 初始化嵌入窗口属性
        self.embedded_hwnd = None  # 嵌入的游戏窗口句柄
        self.original_parent = None  # 原始父窗口句柄
        self.original_pos = None  # 原始窗口位置
        self.original_size = None  # 原始窗口大小
        self.original_style = None  # 原始窗口样式
        
        # 将左右框架添加到paned window
        self.paned_window.add(left_frame, weight=2)  # 左侧功能区域占2份
        self.paned_window.add(self.right_frame, weight=3)  # 右侧区域占3份
        
        # 底部状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def toggle_log_visibility(self):
        """切换日志区域的显示状态"""
        if self.log_visible.get():
            # 显示日志区域
            self.log_content_frame.pack(fill=tk.BOTH, expand=True)
            # 调整paned window的权重
            self.paned_window.configure(weights=(2, 3))
            self.log("日志区域已显示")
        else:
            # 隐藏日志区域
            self.log_content_frame.pack_forget()
            # 调整paned window的权重，让左侧功能区域占满整个窗口
            self.paned_window.configure(weights=(1, 0))
            self.log("日志区域已隐藏")
    
    def load_scripts(self):
        """加载本地脚本"""
        self.scripts = []
        
        # 处理PyInstaller打包后的路径问题
        if getattr(sys, 'frozen', False):
            # 运行在PyInstaller打包后的环境中
            project_root = os.path.dirname(sys.executable)
            print(f"[DEBUG] 打包环境 - 项目根目录: {project_root}")
        else:
            # 直接运行Python脚本
            project_root = os.path.dirname(os.path.abspath(__file__))
            print(f"[DEBUG] 脚本环境 - 项目根目录: {project_root}")
        
        self.log(f"项目根目录: {project_root}")
        
        # 搜索twinkle_starknightsX/daily目录下的脚本
        daily_script_path = os.path.join(project_root, "twinkle_starknightsX", "daily", "daily.py")
        print(f"[DEBUG] 检查日常脚本路径: {daily_script_path}")
        self.log(f"检查日常脚本路径: {daily_script_path}")
        if os.path.exists(daily_script_path):
            print(f"[DEBUG] 找到日常脚本: {daily_script_path}")
            self.log(f"找到日常脚本: {daily_script_path}")
            self.scripts.append({
                "name": "日常任务脚本",
                "path": daily_script_path,
                "status": "就绪"
            })
        else:
            print(f"[DEBUG] 未找到日常脚本: {daily_script_path}")
            self.log(f"未找到日常脚本: {daily_script_path}")
        
        # 搜索Girls_Creation_script/dungeon目录下的脚本
        dungeon_script_path = os.path.join(project_root, "Girls_Creation_script", "dungeon", "dungeon.py")
        print(f"[DEBUG] 检查地牢脚本路径: {dungeon_script_path}")
        self.log(f"检查地牢脚本路径: {dungeon_script_path}")
        if os.path.exists(dungeon_script_path):
            print(f"[DEBUG] 找到地牢脚本: {dungeon_script_path}")
            self.log(f"找到地牢脚本: {dungeon_script_path}")
            self.scripts.append({
                "name": "地牢脚本",
                "path": dungeon_script_path,
                "status": "就绪"
            })
        else:
            print(f"[DEBUG] 未找到地牢脚本: {dungeon_script_path}")
            self.log(f"未找到地牢脚本: {dungeon_script_path}")
        
        # 如果没有找到脚本，尝试搜索当前目录的父目录
        if len(self.scripts) == 0:
            print(f"[DEBUG] 没有找到脚本，尝试搜索父目录")
            parent_root = os.path.dirname(project_root)
            print(f"[DEBUG] 父目录: {parent_root}")
            
            # 再次尝试搜索脚本
            daily_script_path = os.path.join(parent_root, "twinkle_starknightsX", "daily", "daily.py")
            if os.path.exists(daily_script_path):
                self.scripts.append({
                    "name": "日常任务脚本",
                    "path": daily_script_path,
                    "status": "就绪"
                })
            
            dungeon_script_path = os.path.join(parent_root, "Girls_Creation_script", "dungeon", "dungeon.py")
            if os.path.exists(dungeon_script_path):
                self.scripts.append({
                    "name": "地牢脚本",
                    "path": dungeon_script_path,
                    "status": "就绪"
                })
        
        # 搜索当前目录下的测试脚本
        test_script_path = os.path.join(project_root, "test_embed_operation.py")
        print(f"[DEBUG] 检查测试脚本路径: {test_script_path}")
        self.log(f"检查测试脚本路径: {test_script_path}")
        if os.path.exists(test_script_path):
            print(f"[DEBUG] 找到测试脚本: {test_script_path}")
            self.log(f"找到测试脚本: {test_script_path}")
            self.scripts.append({
                "name": "嵌入窗口测试脚本",
                "path": test_script_path,
                "status": "就绪"
            })
        else:
            print(f"[DEBUG] 未找到测试脚本: {test_script_path}")
            self.log(f"未找到测试脚本: {test_script_path}")
        
        print(f"[DEBUG] 总共加载脚本数量: {len(self.scripts)}")
        self.log(f"总共加载脚本数量: {len(self.scripts)}")
        
        # 更新脚本列表
        self.update_script_tree()
        print(f"[DEBUG] 脚本列表已更新")
    
    def update_script_tree(self):
        """更新脚本列表Treeview"""
        print(f"[DEBUG] 更新脚本列表，当前脚本数量: {len(self.scripts)}")
        
        # 清空现有内容
        children = self.script_tree.get_children()
        print(f"[DEBUG] 清空前Treeview子项数量: {len(children)}")
        for item in children:
            self.script_tree.delete(item)
        
        # 添加脚本
        for i, script in enumerate(self.scripts):
            print(f"[DEBUG] 插入脚本 {i+1}: {script['name']}")
            self.script_tree.insert("", tk.END, values=(script["name"], script["path"], script["status"]))
        
        # 检查插入后的子项数量
        children_after = self.script_tree.get_children()
        print(f"[DEBUG] 插入后Treeview子项数量: {len(children_after)}")
        
        # 打印所有插入的脚本
        for item in children_after:
            values = self.script_tree.item(item, "values")
            print(f"[DEBUG] Treeview中的脚本: {values}")
    
    def browse_game_path(self):
        """浏览游戏路径"""
        game_path = filedialog.askopenfilename(
            title="选择游戏可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if game_path:
            self.game_path_entry.delete(0, tk.END)
            self.game_path_entry.insert(0, game_path)
    
    def select_game_window(self):
        """启动游戏窗口选择模式"""
        self.log("启动游戏窗口选择模式")
        self.window_hint_label.config(text="请移动鼠标到游戏窗口上，按下Alt键选择窗口...")
        
        # 创建一个半透明的顶层窗口用于显示提示信息
        self.select_window = tk.Toplevel(self.root)
        self.select_window.attributes("-alpha", 0.7)
        self.select_window.attributes("-topmost", True)
        self.select_window.overrideredirect(True)
        self.select_window.geometry("300x100+100+100")
        
        # 设置背景色和文本
        canvas = tk.Canvas(self.select_window, bg="black", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_text(150, 50, text="鼠标移动到游戏窗口上，按下Alt键选择", 
                          fill="white", font=("微软雅黑", 12), anchor="center")
        
        # 开始鼠标跟踪
        self.is_selecting = True
        self.root.after(100, self.track_mouse)
        
        # 绑定Alt键事件
        self.root.bind("<Alt_L>", self.on_alt_press)
        self.root.bind("<Alt_R>", self.on_alt_press)
    
    def embed_game_window(self):
        """将游戏窗口嵌入到脚本管理器"""
        self.log("尝试嵌入游戏窗口", "debug")
        
        # 获取游戏标题
        game_title = self.game_title_entry.get().strip()
        if not game_title:
            self.log("未输入游戏标题，无法嵌入窗口", "warning")
            messagebox.showwarning("警告", "请先选择游戏窗口或输入游戏标题")
            return
        
        # 查找游戏窗口
        self.log(f"正在查找游戏窗口：{game_title}", "debug")
        hwnd = win32gui.FindWindow(None, game_title)
        if hwnd == 0:
            self.log(f"未找到游戏窗口：{game_title}", "error")
            messagebox.showwarning("警告", f"未找到游戏窗口：{game_title}")
            return
        
        self.log(f"找到游戏窗口，句柄：{hwnd}", "info")
        
        # 保存原始窗口信息
        self.log(f"保存原始窗口信息：句柄={hwnd}", "debug")
        self.original_parent = win32gui.GetParent(hwnd)
        self.original_pos = win32gui.GetWindowRect(hwnd)
        self.original_size = (self.original_pos[2] - self.original_pos[0], 
                             self.original_pos[3] - self.original_pos[1])
        self.original_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        
        self.log(f"原始窗口信息：父窗口={self.original_parent}, 位置={self.original_pos}, 大小={self.original_size}, 样式={hex(self.original_style)}", "debug")
        
        # 获取嵌入容器的句柄
        embed_hwnd = self.embed_frame.winfo_id()
        self.log(f"嵌入容器句柄：{embed_hwnd}", "debug")
        
        try:
            # 设置游戏窗口为嵌入容器的子窗口
            self.log(f"设置游戏窗口父窗口为嵌入容器：{hwnd} -> {embed_hwnd}", "debug")
            win32gui.SetParent(hwnd, embed_hwnd)
            
            # 调整窗口样式，保留必要的样式以确保能接收鼠标消息
            # 获取当前窗口样式
            current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            # 保留一些必要的样式，添加子窗口样式
            new_style = (current_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME | win32con.WS_SYSMENU)) | \
                        win32con.WS_CHILD | win32con.WS_VISIBLE | win32con.WS_CLIPSIBLINGS | win32con.WS_CLIPCHILDREN
            self.log(f"修改窗口样式：{hex(current_style)} -> {hex(new_style)}", "debug")
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
            
            # 调整窗口大小以适应嵌入容器
            self.embed_frame.update_idletasks()
            width = self.embed_frame.winfo_width()
            height = self.embed_frame.winfo_height()
            self.log(f"调整嵌入窗口大小：{width}x{height}", "debug")
            win32gui.MoveWindow(hwnd, 0, 0, width, height, True)
            
            # 保存嵌入的窗口句柄
            self.embedded_hwnd = hwnd
            
            # 添加大小调整绑定
            self.embed_frame.bind("<Configure>", self.on_embed_frame_resize)
            
            self.log(f"游戏窗口已成功嵌入：{game_title}", "info")
            self.status_var.set(f"游戏窗口已嵌入：{game_title}")
            
            # 切换到游戏嵌入标签页
            self.right_notebook.select(1)  # 1是游戏嵌入标签页的索引
            
        except Exception as e:
            self.log(f"嵌入游戏窗口失败：{str(e)}", "error")
            messagebox.showerror("错误", f"嵌入游戏窗口失败：{str(e)}")
    
    def unembed_game_window(self):
        """取消嵌入游戏窗口，恢复原状态"""
        if not self.embedded_hwnd:
            messagebox.showinfo("提示", "没有已嵌入的游戏窗口")
            return
        
        try:
            self.log(f"开始取消嵌入游戏窗口，句柄：{self.embedded_hwnd}", "debug")
            
            # 恢复原始父窗口
            if self.original_parent:
                self.log(f"恢复原始父窗口：{self.original_parent}", "debug")
                win32gui.SetParent(self.embedded_hwnd, self.original_parent)
            else:
                self.log("恢复父窗口为None", "debug")
                win32gui.SetParent(self.embedded_hwnd, None)
            
            # 恢复原始窗口样式
            self.log(f"恢复原始窗口样式：{hex(self.original_style)}", "debug")
            win32gui.SetWindowLong(self.embedded_hwnd, win32con.GWL_STYLE, self.original_style)
            
            # 恢复原始窗口位置和大小
            self.log(f"恢复原始窗口位置和大小：{self.original_pos} -> {self.original_size}", "debug")
            win32gui.MoveWindow(self.embedded_hwnd, 
                              self.original_pos[0], self.original_pos[1], 
                              self.original_size[0], self.original_size[1], True)
            
            # 显示窗口
            self.log("显示并激活窗口", "debug")
            win32gui.ShowWindow(self.embedded_hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(self.embedded_hwnd)
            
            self.log("游戏窗口已成功取消嵌入", "info")
            self.status_var.set("游戏窗口已取消嵌入")
            
            # 清除嵌入状态
            self.embedded_hwnd = None
            self.original_parent = None
            self.original_pos = None
            self.original_size = None
            self.original_style = None
            
            # 移除大小调整绑定
            self.embed_frame.unbind("<Configure>")
            
        except Exception as e:
            self.log(f"取消嵌入游戏窗口失败：{str(e)}", "error")
            messagebox.showerror("错误", f"取消嵌入游戏窗口失败：{str(e)}")
    
    def on_embed_frame_resize(self, event):
        """嵌入容器大小改变时，调整游戏窗口大小"""
        if not self.embedded_hwnd:
            return
        
        try:
            # 获取新的容器大小
            width = event.width
            height = event.height
            
            # 调整游戏窗口大小
            self.log(f"调整嵌入窗口大小：{width}x{height}", "debug")
            win32gui.MoveWindow(self.embedded_hwnd, 0, 0, width, height, True)
            
        except Exception as e:
            self.log(f"调整嵌入窗口大小失败：{str(e)}", "error")
    
    def track_mouse(self):
        """跟踪鼠标位置，显示当前指向的窗口"""
        if not hasattr(self, 'is_selecting') or not self.is_selecting:
            return
        
        try:
            # 获取鼠标位置
            x, y = win32gui.GetCursorPos()
            
            # 获取鼠标下的窗口句柄
            hwnd = win32gui.WindowFromPoint((x, y))
            
            if hwnd > 0:
                # 获取窗口标题
                title = win32gui.GetWindowText(hwnd)
                
                # 更新提示窗口位置和内容
                self.select_window.geometry(f"300x100+{x+20}+{y+20}")
                
                # 更新状态标签
                self.window_hint_label.config(text=f"当前窗口: {title} (句柄: {hwnd})")
        except Exception as e:
            self.log(f"鼠标跟踪错误: {str(e)}")
        
        # 继续跟踪
        if self.is_selecting:
            self.root.after(100, self.track_mouse)
    
    def on_alt_press(self, event):
        """处理Alt键按下事件，选择当前鼠标下的窗口"""
        if not hasattr(self, 'is_selecting') or not self.is_selecting:
            return
        
        try:
            # 获取鼠标位置
            x, y = win32gui.GetCursorPos()
            
            # 获取鼠标下的窗口句柄
            hwnd = win32gui.WindowFromPoint((x, y))
            
            if hwnd > 0:
                # 获取窗口标题
                title = win32gui.GetWindowText(hwnd)
                
                if title:
                    # 获取窗口对应的进程ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    # 获取进程路径
                    game_path = self.get_process_path(pid)
                    
                    # 更新UI
                    self.game_title_entry.delete(0, tk.END)
                    self.game_title_entry.insert(0, title)
                    
                    if game_path:
                        self.game_path_entry.delete(0, tk.END)
                        self.game_path_entry.insert(0, game_path)
                    
                    self.log(f"已选择游戏窗口: {title} (路径: {game_path})")
                    self.window_hint_label.config(text=f"已选择窗口: {title}")
                else:
                    self.log("未获取到窗口标题")
                    self.window_hint_label.config(text="未获取到窗口标题，请重新选择")
        except Exception as e:
            self.log(f"选择窗口错误: {str(e)}")
            self.window_hint_label.config(text=f"选择窗口错误: {str(e)}")
        finally:
            # 结束选择模式
            self.is_selecting = False
            
            # 解绑Alt键
            self.root.unbind("<Alt_L>")
            self.root.unbind("<Alt_R>")
            
            # 销毁提示窗口
            if hasattr(self, 'select_window'):
                self.select_window.destroy()
    
    def get_process_path(self, pid):
        """根据进程ID获取进程路径"""
        try:
            process = psutil.Process(pid)
            return process.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self.log(f"获取进程路径失败: {str(e)}")
            return None
    
    def run_script(self):
        """运行选中的脚本，支持后台模式"""
        # 获取选中的脚本
        selected_item = self.script_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个脚本")
            return
        
        # 获取脚本信息
        item = selected_item[0]
        values = self.script_tree.item(item, "values")
        script_name = values[0]
        script_path = values[1]
        
        # 检查脚本是否已经在运行
        for script in self.scripts:
            if script["path"] == script_path:
                if script["status"] == "运行中":
                    messagebox.showinfo("提示", "脚本已经在运行中")
                    return
                
                # 获取运行模式
                mode = self.run_mode.get()
                self.log(f"运行模式：{mode}")
                
                game_process = None
                game_hwnd = None
                
                # 获取游戏信息
                game_path = self.game_path_entry.get().strip()
                game_title = self.game_title_entry.get().strip()
                
                # 优先使用已经嵌入的游戏窗口
                if self.embedded_hwnd:
                    game_hwnd = self.embedded_hwnd
                    game_process = None
                    self.log(f"使用已嵌入的游戏窗口，句柄：{game_hwnd}")
                    self.log(f"运行模式：{mode}")
                elif mode == "background":
                    # 后台模式：先尝试连接已打开的窗口
                    self.log(f"尝试连接已打开的游戏窗口：{game_title}")
                    game_hwnd = win32gui.FindWindow(None, game_title)
                    
                    if game_hwnd > 0:
                        # 找到已打开的窗口，直接连接
                        self.log(f"找到已打开的游戏窗口，句柄：{game_hwnd}")
                        # 如果不是嵌入窗口，才设置为后台模式
                        try:
                            # 设置窗口为分层透明
                            current_style = win32gui.GetWindowLong(game_hwnd, win32con.GWL_EXSTYLE)
                            win32gui.SetWindowLong(game_hwnd, win32con.GWL_EXSTYLE, 
                                                 current_style | win32con.WS_EX_LAYERED)
                            
                            # 设置窗口透明度为0（完全透明）
                            win32gui.SetLayeredWindowAttributes(game_hwnd, 0, 0, win32con.LWA_ALPHA)
                            self.log("游戏窗口已设置为完全透明")
                            
                            # 将窗口移动到屏幕外
                            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                            win32gui.MoveWindow(game_hwnd, screen_width + 100, screen_height + 100, 
                                               800, 600, True)
                            self.log("游戏窗口已移动到屏幕外")
                        except Exception as e:
                            self.log(f"设置窗口后台模式失败：{str(e)}")
                            # 失败时降级为最小化窗口
                            win32gui.ShowWindow(game_hwnd, win32con.SW_MINIMIZE)
                            self.log("已降级为最小化窗口模式")
                    else:
                        # 未找到已打开的窗口，启动新的游戏进程
                        if not game_path:
                            messagebox.showwarning("警告", "请输入游戏路径")
                            return
                        
                        if not os.path.exists(game_path):
                            messagebox.showwarning("警告", f"游戏路径不存在：{game_path}")
                            return
                        
                        if not game_title:
                            messagebox.showwarning("警告", "请输入游戏标题")
                            return
                        
                        self.log(f"未找到已打开的窗口，启动新的游戏进程：{game_path}")
                        game_process, game_hwnd = self.manage_game_process(game_path, game_title, mode)
                
                # 更新脚本状态
                script["status"] = "运行中"
                self.update_script_tree()
                
                # 创建线程运行脚本
                thread = threading.Thread(
                    target=self._run_script_in_thread, 
                    args=(script, game_process, game_hwnd, mode), 
                    daemon=True
                )
                thread.start()
                
                self.status_var.set(f"正在运行脚本：{script_name}")
                self.log(f"开始运行脚本：{script_name}")
                break
    
    def manage_game_process(self, game_path, game_title, mode="background"):
        """管理游戏进程，返回进程对象和窗口句柄"""
        self.log(f"管理游戏进程：{game_path}，标题：{game_title}，模式：{mode}")
        
        # 启动游戏进程
        game_process = subprocess.Popen([game_path])
        
        # 等待窗口出现
        self.log("等待游戏窗口出现...")
        time.sleep(3)
        
        # 获取窗口句柄
        hwnd = win32gui.FindWindow(None, game_title)
        
        if hwnd == 0:
            self.log(f"未找到游戏窗口：{game_title}")
            return game_process, None
        
        self.log(f"找到游戏窗口，句柄：{hwnd}")
        
        if mode == "background":
            # 后台模式：使用窗口透明度设置为0，而不是隐藏窗口
            # 这样Airtest可以正常截图，同时窗口对用户不可见
            try:
                # 获取窗口当前风格
                current_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
                
                # 设置窗口为分层透明
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, 
                                     current_style | win32con.WS_EX_LAYERED)
                
                # 设置窗口透明度为0（完全透明）
                win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_ALPHA)
                self.log("游戏窗口已设置为完全透明")
                
                # 将窗口移动到屏幕外，确保不占用可见空间
                # 获取主显示器尺寸
                import win32api
                screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                
                # 将窗口移动到屏幕右下方外部
                win32gui.MoveWindow(hwnd, screen_width + 100, screen_height + 100, 
                                   800, 600, True)
                self.log("游戏窗口已移动到屏幕外")
            except Exception as e:
                self.log(f"设置窗口后台模式失败：{str(e)}")
                # 失败时降级为最小化窗口
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                self.log("已降级为最小化窗口模式")
        else:
            # 正常模式：显示并激活窗口
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            win32gui.SetForegroundWindow(hwnd)
            self.log("游戏窗口已显示并激活")
        
        return game_process, hwnd
    
    def get_window_info(self, hwnd):
        """获取窗口信息"""
        if hwnd is None:
            return None
        
        try:
            # 获取窗口标题
            title = win32gui.GetWindowText(hwnd)
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
            return {
                "hwnd": hwnd,
                "title": title,
                "rect": rect
            }
        except Exception as e:
            self.log(f"获取窗口信息失败：{str(e)}")
            return None
    
    def _run_script_in_thread(self, script, game_process=None, game_hwnd=None, mode="normal"):
        """在子线程中运行脚本，支持后台模式"""
        try:
            # 准备脚本命令参数
            cmd_args = [self.venv_python, script['path']]
            
            # 如果有游戏窗口，传递窗口信息给脚本（无论模式如何）
            if game_hwnd:
                # 获取游戏窗口标题
                game_title = win32gui.GetWindowText(game_hwnd)
                
                # 将窗口标题和后台模式作为参数传递给脚本
                cmd_args.append(f"--window-title={game_title}")
                cmd_args.append(f"--window-hwnd={game_hwnd}")
                cmd_args.append(f"--bg-mode={self.bg_run_mode.get()}")
                
                # 只向测试脚本传递嵌入状态参数
                script_name = os.path.basename(script['path'])
                if script_name == 'test_embed_operation.py':
                    # 检查窗口是否为嵌入窗口
                    is_embedded = win32gui.GetParent(game_hwnd) is not None
                    cmd_args.append(f"--is-embedded={is_embedded}")
                    self.log(f"传递嵌入状态参数：{is_embedded}", "debug")
                
                self.log(f"传递窗口标题参数：{game_title}", "debug")
                self.log(f"传递窗口句柄参数：{game_hwnd}", "debug")
                self.log(f"传递后台模式参数：{self.bg_run_mode.get()}", "debug")
                
                # 传递运行模式
                cmd_args.append(f"--run-mode={mode}")
                self.log(f"传递运行模式参数：{mode}", "debug")
            
            self.log(f"执行命令：{' '.join(cmd_args)}")
            
            # 使用subprocess运行脚本，捕获输出
            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 保存进程引用
            self.running_scripts[script['path']] = {
                "script_process": process,
                "game_process": game_process,
                "game_hwnd": game_hwnd,
                "mode": mode
            }
            
            # 启动监控线程
            monitor_thread = threading.Thread(
                target=self.monitor_processes,
                args=(process, game_process, script),
                daemon=True
            )
            monitor_thread.start()
            
            # 读取输出
            for line in process.stdout:
                self.log(line.strip())
            
            # 等待进程结束
            process.wait()
            
            # 更新状态
            script["status"] = "就绪"
            self.running_scripts.pop(script['path'], None)
            
            if process.returncode == 0:
                self.log(f"脚本执行成功：{script['name']}")
            else:
                self.log(f"脚本执行失败，返回码：{process.returncode}")
                messagebox.showerror("错误", f"脚本执行失败：{script['name']}")
                
        except Exception as e:
            script["status"] = "就绪"
            self.running_scripts.pop(script['path'], None)
            self.log(f"脚本执行错误：{str(e)}")
            messagebox.showerror("错误", f"脚本执行错误：{str(e)}")
        
        finally:
            # 清理游戏进程（仅当是我们启动的进程时才终止）
            if game_process:
                try:
                    if game_process.poll() is None:  # 检查进程是否仍在运行
                        game_process.terminate()
                        self.log("游戏进程已终止")
                except Exception as e:
                    self.log(f"终止游戏进程失败：{str(e)}")
            
            # 如果是直接连接的窗口，恢复窗口状态
            if game_hwnd and not game_process and mode == "background":
                try:
                    # 恢复窗口透明度和位置
                    # 移除分层样式
                    current_style = win32gui.GetWindowLong(game_hwnd, win32con.GWL_EXSTYLE)
                    win32gui.SetWindowLong(game_hwnd, win32con.GWL_EXSTYLE, 
                                         current_style & ~win32con.WS_EX_LAYERED)
                    
                    # 显示窗口
                    win32gui.ShowWindow(game_hwnd, win32con.SW_SHOW)
                    
                    # 移动窗口到屏幕内
                    win32gui.MoveWindow(game_hwnd, 100, 100, 800, 600, True)
                    
                    self.log("已恢复游戏窗口状态")
                except Exception as e:
                    self.log(f"恢复窗口状态失败：{str(e)}")
            
            self.root.after(0, self.update_script_tree)
            self.root.after(0, lambda: self.status_var.set("就绪"))
    
    def get_process_info(self, process):
        """获取进程信息"""
        if process is None:
            return None
        
        try:
            p = psutil.Process(process.pid)
            return {
                "pid": process.pid,
                "name": p.name(),
                "cpu_percent": p.cpu_percent(interval=0.1),
                "memory_percent": p.memory_percent(),
                "status": p.status()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.log(f"获取进程信息失败：{str(e)}")
            return None
    
    def handle_exception(self, process_type, return_code, script=None):
        """处理进程异常"""
        self.log(f"进程异常：{process_type} 返回码：{return_code}")
        
        # 更新脚本状态
        if script:
            script["status"] = "就绪"
            self.root.after(0, self.update_script_tree)
        
        # 记录详细日志
        error_msg = f"{process_type} 进程出现故障，返回码：{return_code}"
        self.log(f"错误：{error_msg}")
        
        # 发送通知
        messagebox.showerror("进程异常", error_msg)
    
    def monitor_processes(self, script_process, game_process, script):
        """监控脚本和游戏进程状态"""
        self.log("启动进程监控")
        
        while True:
            time.sleep(5)  # 每5秒检测一次
            
            try:
                # 检查脚本进程
                script_alive = script_process.poll() is None
                script_info = self.get_process_info(script_process) if script_alive else None
                
                # 检查游戏进程
                game_alive = game_process.poll() is None if game_process else True
                game_info = self.get_process_info(game_process) if game_process and game_alive else None
                
                # 记录状态
                if script_info:
                    self.log(f"脚本进程状态：PID={script_info['pid']}, CPU={script_info['cpu_percent']:.1f}%, 内存={script_info['memory_percent']:.1f}%, 状态={script_info['status']}")
                
                if game_info:
                    self.log(f"游戏进程状态：PID={game_info['pid']}, CPU={game_info['cpu_percent']:.1f}%, 内存={game_info['memory_percent']:.1f}%, 状态={game_info['status']}")
                
                # 异常处理
                if not script_alive:
                    self.handle_exception("脚本", script_process.returncode, script)
                    break
                
                if game_process and not game_alive:
                    self.handle_exception("游戏", game_process.returncode, script)
                    # 终止脚本进程
                    script_process.terminate()
                    break
                    
            except Exception as e:
                self.log(f"监控进程时发生错误：{str(e)}")
                time.sleep(2)  # 错误后暂停2秒再继续监控
    
    def stop_script(self):
        """停止选中的脚本"""
        # 获取选中的脚本
        selected_item = self.script_tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个脚本")
            return
        
        # 获取脚本信息
        item = selected_item[0]
        values = self.script_tree.item(item, "values")
        script_name = values[0]
        script_path = values[1]
        
        # 检查脚本是否在运行
        if script_path not in self.running_scripts:
            messagebox.showinfo("提示", "脚本未在运行")
            return
        
        # 停止脚本
        process_info = self.running_scripts[script_path]
        script_process = process_info["script_process"]
        game_process = process_info["game_process"]
        
        # 终止脚本进程
        script_process.terminate()
        
        # 终止游戏进程
        if game_process and not game_process.poll():
            game_process.terminate()
            self.log("游戏进程已终止")
        
        # 更新状态
        for script in self.scripts:
            if script["path"] == script_path:
                script["status"] = "就绪"
                break
        
        # 更新UI
        self.update_script_tree()
        self.status_var.set("就绪")
        self.log(f"脚本已停止：{script_name}")
    
    def refresh_scripts(self):
        """刷新脚本列表"""
        self.load_scripts()
        self.log("脚本列表已刷新")
    
    def add_script(self):
        """添加新脚本"""
        # 打开文件选择对话框
        script_path = filedialog.askopenfilename(
            title="选择Python脚本",
            filetypes=[("Python Files", "*.py")],
            initialdir=os.path.dirname(os.path.abspath(__file__))
        )
        
        if script_path:
            # 获取脚本名称
            script_name = os.path.basename(script_path)
            script_name = os.path.splitext(script_name)[0]
            
            # 添加脚本
            self.scripts.append({
                "name": script_name,
                "path": script_path,
                "status": "就绪"
            })
            
            # 更新UI
            self.update_script_tree()
            self.log(f"已添加脚本：{script_name}")
    
    def log(self, message, level="info"):
        """添加日志信息"""
        self.log_queue.put((message, level))
        
        # 同时写入日志文件
        if level == "debug":
            logger.debug(message)
        elif level == "warning":
            logger.warning(message)
        elif level == "error":
            logger.error(message)
        else:
            logger.info(message)
    
    def update_logs(self):
        """更新日志显示"""
        # 从队列中获取日志
        while not self.log_queue.empty():
            message, level = self.log_queue.get()
            timestamp = time.strftime("%H:%M:%S")
            
            # 根据级别添加不同颜色标记
            if level == "error":
                log_entry = f"[{timestamp}] [ERROR] {message}\n"
            elif level == "warning":
                log_entry = f"[{timestamp}] [WARNING] {message}\n"
            elif level == "debug":
                log_entry = f"[{timestamp}] [DEBUG] {message}\n"
            else:
                log_entry = f"[{timestamp}] {message}\n"
            
            # 在UI中显示日志
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        # 继续定时更新
        self.root.after(100, self.update_logs)

if __name__ == "__main__":
    # 创建主窗口
    root = tk.Tk()
    
    # 创建脚本管理器实例
    app = ScriptManager(root)
    
    # 运行主循环
    root.mainloop()
