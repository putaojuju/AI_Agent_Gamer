# -*- coding: utf-8 -*-
"""
游戏脚本管理器 - 可视化UI (优化版)
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
import ctypes
from ctypes import wintypes

# DWM Thumbnail API 定义
dwmapi = ctypes.WinDLL('dwmapi')

# DWM缩略图结构定义
class DWM_THUMBNAIL_PROPERTIES(ctypes.Structure):
    _fields_ = [
        ('dwFlags', wintypes.DWORD),
        ('rcDestination', wintypes.RECT),
        ('rcSource', wintypes.RECT),
        ('opacity', wintypes.BYTE),
        ('fVisible', wintypes.BOOL),
        ('fSourceClientAreaOnly', wintypes.BOOL),
    ]

# DWM缩略图标志
dwmapi.DWM_TNP_RECTDESTINATION = 0x00000001
dwmapi.DWM_TNP_RECTSOURCE = 0x00000002
dwmapi.DWM_TNP_OPACITY = 0x00000004
dwmapi.DWM_TNP_VISIBLE = 0x00000008
dwmapi.DWM_TNP_SOURCECLIENTAREAONLY = 0x00000010

# 窗口矩形结构
class RECT(ctypes.Structure):
    _fields_ = [
        ('left', wintypes.LONG),
        ('top', wintypes.LONG),
        ('right', wintypes.LONG),
        ('bottom', wintypes.LONG),
    ]

# 配置日志系统
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'script_manager.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScriptManager:
    def __init__(self, root):
        self.root = root
        self.root.title("游戏脚本管理器 Pro")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
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
        
        # 初始化嵌入窗口属性
        self.embedded_hwnd = None
        self.original_parent = None
        self.original_pos = None
        self.original_size = None
        self.original_style = None
        self.dwm_thumbnail = None
        self.using_dwm = False
        
        # 设置样式
        self.setup_styles()
        
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
    
    def setup_styles(self):
        """配置ttk样式"""
        style = ttk.Style()
        style.theme_use('clam')  # 使用clam主题作为基础
        
        # 定义颜色
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_light': '#f0f0f0',
            'fg_dark': '#ffffff',
            'fg_light': '#000000',
            'accent': '#007acc',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545'
        }
        
        # 默认使用浅色模式
        self.is_dark_mode = False
        
        # 配置Treeview样式
        style.configure("Treeview", rowheight=25)
        style.configure("Treeview.Heading", font=('微软雅黑', 9, 'bold'))
        
        # 配置按钮样式
        style.configure("Action.TButton", font=('微软雅黑', 9))
        style.configure("Primary.TButton", font=('微软雅黑', 9, 'bold'), foreground=self.colors['accent'])
        
        # 配置标签样式
        style.configure("Header.TLabel", font=('微软雅黑', 12, 'bold'))
        style.configure("Status.TLabel", font=('微软雅黑', 9))
    
    def create_widgets(self):
        """创建现代化UI布局"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部工具栏
        toolbar = ttk.Frame(main_container, padding=5)
        toolbar.pack(fill=tk.X, side=tk.TOP)
        
        ttk.Label(toolbar, text="脚本管理器", style="Header.TLabel").pack(side=tk.LEFT, padx=5)
        
        # 状态指示器
        self.status_indicator = ttk.Label(toolbar, text="● 就绪", foreground="green", style="Status.TLabel")
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
        # 分割窗格 (左侧列表 | 右侧内容)
        self.paned_window = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === 左侧区域：脚本列表 ===
        left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(left_panel, weight=1)
        
        # 脚本列表容器
        list_frame = ttk.LabelFrame(left_panel, text="脚本列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 脚本Treeview
        columns = ("name", "status")
        self.script_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.script_tree.heading("name", text="脚本名称")
        self.script_tree.heading("status", text="状态")
        self.script_tree.column("name", width=150)
        self.script_tree.column("status", width=60)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscroll=scrollbar.set)
        
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 底部按钮区
        btn_frame = ttk.Frame(left_panel, padding=5)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="运行", command=self.run_script, style="Primary.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="停止", command=self.stop_script).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="刷新", command=self.refresh_scripts).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(btn_frame, text="+", width=3, command=self.add_script).pack(side=tk.LEFT, padx=2)
        
        # === 右侧区域：游戏预览与控制 ===
        right_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(right_panel, weight=3)
        
        # 垂直分割 (上：游戏预览 | 下：控制台)
        right_split = ttk.PanedWindow(right_panel, orient=tk.VERTICAL)
        right_split.pack(fill=tk.BOTH, expand=True)
        
        # 1. 游戏预览区域
        preview_frame = ttk.LabelFrame(right_split, text="游戏窗口预览", padding=5)
        right_split.add(preview_frame, weight=3)
        
        # 嵌入容器
        self.embed_frame = tk.Frame(preview_frame, bg="black")
        self.embed_frame.pack(fill=tk.BOTH, expand=True)
        
        # 预览控制栏
        preview_ctrl = ttk.Frame(preview_frame)
        preview_ctrl.pack(fill=tk.X, pady=2)
        
        ttk.Button(preview_ctrl, text="选择窗口", command=self.select_game_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(preview_ctrl, text="嵌入", command=self.embed_game_window).pack(side=tk.LEFT, padx=2)
        ttk.Button(preview_ctrl, text="弹出", command=self.unembed_game_window).pack(side=tk.LEFT, padx=2)
        
        self.game_title_entry = ttk.Entry(preview_ctrl)
        self.game_title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.game_title_entry.insert(0, "输入游戏标题或使用选择按钮")
        
        # 2. 控制台区域 (Tab页)
        console_frame = ttk.Frame(right_split)
        right_split.add(console_frame, weight=2)
        
        self.notebook = ttk.Notebook(console_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: 运行日志
        log_tab = ttk.Frame(self.notebook)
        self.notebook.add(log_tab, text="运行日志")
        
        self.log_text = tk.Text(log_tab, font=("Consolas", 9), state=tk.DISABLED, wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(log_tab, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Tab 2: 运行配置
        settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_tab, text="运行配置")
        
        # 运行模式
        mode_group = ttk.LabelFrame(settings_tab, text="运行模式", padding=10)
        mode_group.pack(fill=tk.X, pady=5)
        
        self.run_mode = tk.StringVar(value="normal")
        ttk.Radiobutton(mode_group, text="主屏幕模式 (正常游玩)", variable=self.run_mode, value="normal", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_group, text="监控模式 (虚拟屏运行+预览)", variable=self.run_mode, value="monitor", command=self.on_mode_change).pack(anchor=tk.W)
        ttk.Radiobutton(mode_group, text="后台模式 (完全隐藏)", variable=self.run_mode, value="background", command=self.on_mode_change).pack(anchor=tk.W)
        
        # 后台选项
        bg_group = ttk.LabelFrame(settings_tab, text="后台选项", padding=10)
        bg_group.pack(fill=tk.X, pady=5)
        
        self.bg_run_mode = tk.StringVar(value="message")
        ttk.Label(bg_group, text="实现方式:").pack(side=tk.LEFT)
        ttk.Combobox(bg_group, textvariable=self.bg_run_mode, values=["message", "transparent", "minimize", "hide"], state="readonly", width=15).pack(side=tk.LEFT, padx=5)
        ttk.Label(bg_group, text="(推荐使用消息模式)", foreground="gray").pack(side=tk.LEFT)
        
        # 游戏路径
        path_group = ttk.LabelFrame(settings_tab, text="游戏路径 (自动启动用)", padding=10)
        path_group.pack(fill=tk.X, pady=5)
        
        self.game_path_entry = ttk.Entry(path_group)
        self.game_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_group, text="浏览", command=self.browse_game_path).pack(side=tk.LEFT, padx=5)
        
        # 底部状态栏
        self.status_var = tk.StringVar(value="系统就绪")
        status_bar = ttk.Label(main_container, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=2)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # ==================== 核心逻辑方法 (保持原有功能) ====================

    def log(self, message, level="info"):
        """添加日志信息"""
        self.log_queue.put((message, level))
        if level == "debug": logger.debug(message)
        elif level == "warning": logger.warning(message)
        elif level == "error": logger.error(message)
        else: logger.info(message)

    def update_logs(self):
        """更新日志显示"""
        while not self.log_queue.empty():
            message, level = self.log_queue.get()
            timestamp = time.strftime("%H:%M:%S")
            
            tag = "INFO"
            if level == "error": tag = "ERROR"
            elif level == "warning": tag = "WARN"
            elif level == "debug": tag = "DEBUG"
            
            log_entry = f"[{timestamp}] [{tag}] {message}\n"
            
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(100, self.update_logs)

    def _get_venv_python(self):
        """获取虚拟环境Python解释器路径"""
        project_root = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(project_root, "venv", "Scripts", "python.exe")
        if os.path.exists(venv_python): return venv_python
        if getattr(sys, 'frozen', False): return sys.executable
        return sys.executable

    def check_environment(self):
        """检查环境状态"""
        self.log("正在检查运行环境...")
        try:
            subprocess.check_call([self.venv_python, '-c', 'import airtest, win32gui, numpy, cv2'])
            self.log("环境检查通过：核心依赖已安装")
        except Exception as e:
            self.log(f"环境检查警告：{e}", "warning")

    def load_scripts(self):
        """加载本地脚本"""
        self.scripts = []
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        # 定义搜索路径 (更新为games文件夹结构)
        search_paths = [
            os.path.join(project_root, "games", "twinkle_starknightsX_script", "daily", "daily.py"),
            os.path.join(project_root, "games", "Girls_Creation_script", "dungeon", "dungeon.py"),
            os.path.join(project_root, "test_embed_operation.py")
        ]
        
        # 搜索test_files
        test_files_dir = os.path.join(project_root, "test_files")
        if os.path.exists(test_files_dir):
            for f in os.listdir(test_files_dir):
                if f.endswith(".py"):
                    search_paths.append(os.path.join(test_files_dir, f))

        for path in search_paths:
            if os.path.exists(path):
                name = os.path.basename(path).replace(".py", "")
                # 优化命名显示
                if "daily" in name: name = "日常任务脚本"
                elif "dungeon" in name: name = "地牢脚本"
                
                self.scripts.append({"name": name, "path": path, "status": "就绪"})
        
        self.update_script_tree()

    def update_script_tree(self):
        """更新脚本列表UI"""
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        for script in self.scripts:
            self.script_tree.insert("", tk.END, values=(script["name"], script["status"]))

    def run_script(self):
        """运行选中的脚本"""
        selected = self.script_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个脚本")
            return
            
        item = self.script_tree.item(selected[0])
        script_name = item['values'][0]
        
        # 查找脚本对象
        script = next((s for s in self.scripts if s["name"] == script_name), None)
        if not script: return
        
        if script["status"] == "运行中":
            messagebox.showinfo("提示", "该脚本已在运行中")
            return

        # 准备运行参数
        mode = self.run_mode.get()
        game_title = self.game_title_entry.get()
        game_path = self.game_path_entry.get()
        
        # 尝试获取游戏窗口句柄
        game_hwnd = self.embedded_hwnd
        game_process = None
        
        if not game_hwnd:
            game_hwnd = win32gui.FindWindow(None, game_title)
            if game_hwnd == 0 and mode == "background":
                # 尝试启动游戏
                if game_path and os.path.exists(game_path):
                    self.log(f"启动游戏进程: {game_path}")
                    game_process, game_hwnd = self.manage_game_process(game_path, game_title, mode)
                else:
                    self.log("未找到游戏窗口且未提供有效路径", "warning")
        
        # 检查后台模式是否获取到句柄
        if mode == "background" and not game_hwnd:
            messagebox.showerror("错误", "无法找到游戏窗口，无法启动后台模式。\n请确保游戏已启动或路径正确。")
            self.log("启动失败：后台模式需要有效的窗口句柄", "error")
            return
        
        # 更新状态
        script["status"] = "运行中"
        self.update_script_tree()
        self.status_indicator.config(text="● 运行中", foreground="blue")
        
        # 启动线程
        thread = threading.Thread(
            target=self._run_script_in_thread,
            args=(script, game_process, game_hwnd, mode),
            daemon=True
        )
        thread.start()

    def _run_script_in_thread(self, script, game_process, game_hwnd, mode):
        """后台运行脚本逻辑"""
        try:
            cmd_args = [self.venv_python, script['path']]
            
            if game_hwnd:
                title = win32gui.GetWindowText(game_hwnd)
                cmd_args.extend([
                    f"--window-title={title}",
                    f"--window-hwnd={game_hwnd}",
                    f"--bg-mode={self.bg_run_mode.get()}",
                    f"--run-mode={mode}"
                ])
            
            self.log(f"执行: {' '.join(cmd_args)}")
            
            process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                errors='replace'
            )
            
            self.running_scripts[script['path']] = {
                "process": process,
                "game_process": game_process
            }
            
            # 读取输出
            for line in process.stdout:
                self.log(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                self.log(f"脚本 {script['name']} 执行完成", "success")
            else:
                self.log(f"脚本 {script['name']} 异常退出，代码 {process.returncode}", "error")
                
        except Exception as e:
            self.log(f"运行错误: {e}", "error")
        finally:
            script["status"] = "就绪"
            self.running_scripts.pop(script['path'], None)
            self.root.after(0, self.update_script_tree)
            self.root.after(0, lambda: self.status_indicator.config(text="● 就绪", foreground="green"))

    def stop_script(self):
        """停止脚本"""
        selected = self.script_tree.selection()
        if not selected: return
        
        item = self.script_tree.item(selected[0])
        script_name = item['values'][0]
        script = next((s for s in self.scripts if s["name"] == script_name), None)
        
        if script and script['path'] in self.running_scripts:
            info = self.running_scripts[script['path']]
            info['process'].terminate()
            self.log(f"已停止脚本: {script_name}")

    def refresh_scripts(self):
        self.load_scripts()
        self.log("脚本列表已刷新")

    def add_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            name = os.path.basename(path).replace(".py", "")
            self.scripts.append({"name": name, "path": path, "status": "就绪"})
            self.update_script_tree()

    def browse_game_path(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.game_path_entry.delete(0, tk.END)
            self.game_path_entry.insert(0, path)

    # ==================== 窗口管理与嵌入逻辑 ====================

    def select_game_window(self):
        """启动窗口选择器"""
        self.log("请将鼠标移动到游戏窗口并按 Alt 键...")
        self.status_var.set("等待选择窗口 (按 Alt 确认)...")
        
        self.root.bind("<Alt_L>", self._on_alt_select)
        self.root.bind("<Alt_R>", self._on_alt_select)

    def _on_alt_select(self, event):
        x, y = win32gui.GetCursorPos()
        hwnd = win32gui.WindowFromPoint((x, y))
        if hwnd:
            # 向上查找顶层窗口
            while win32gui.GetParent(hwnd):
                hwnd = win32gui.GetParent(hwnd)
            
            title = win32gui.GetWindowText(hwnd)
            self.game_title_entry.delete(0, tk.END)
            self.game_title_entry.insert(0, title)
            self.log(f"已选择窗口: {title} ({hwnd})")
            self.status_var.set(f"已选择: {title}")
            
            # 解绑
            self.root.unbind("<Alt_L>")
            self.root.unbind("<Alt_R>")

    def embed_game_window(self):
        """嵌入游戏窗口"""
        title = self.game_title_entry.get()
        hwnd = win32gui.FindWindow(None, title)
        if not hwnd:
            messagebox.showerror("错误", "未找到指定窗口")
            return
            
        self.log(f"正在嵌入窗口: {title}")
        
        # 保存原始状态
        self.original_pos = win32gui.GetWindowRect(hwnd)
        self.original_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        self.original_parent = win32gui.GetParent(hwnd)
        
        # 尝试DWM
        embed_hwnd = self.embed_frame.winfo_id()
        if self.create_dwm_thumbnail(hwnd, embed_hwnd):
            self.embedded_hwnd = hwnd
            self.update_dwm_thumbnail()
            self.embed_frame.bind("<Configure>", lambda e: self.update_dwm_thumbnail())
            self.log("使用 DWM Thumbnail 嵌入成功")
        else:
            # 回退 SetParent
            win32gui.SetParent(hwnd, embed_hwnd)
            style = self.original_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
            style |= win32con.WS_CHILD
            win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
            self.embedded_hwnd = hwnd
            self.embed_frame.bind("<Configure>", self._resize_embedded_window)
            self._resize_embedded_window(None)
            self.log("使用 SetParent 嵌入成功")

    def unembed_game_window(self):
        """取消嵌入"""
        if not self.embedded_hwnd: return
        
        if self.using_dwm:
            dwmapi.DwmUnregisterThumbnail(self.dwm_thumbnail)
            self.dwm_thumbnail = None
            self.using_dwm = False
        else:
            win32gui.SetParent(self.embedded_hwnd, self.original_parent)
            win32gui.SetWindowLong(self.embedded_hwnd, win32con.GWL_STYLE, self.original_style)
            
        # 恢复位置
        if self.original_pos:
            l, t, r, b = self.original_pos
            win32gui.MoveWindow(self.embedded_hwnd, l, t, r-l, b-t, True)
            
        self.embedded_hwnd = None
        self.embed_frame.unbind("<Configure>")
        self.log("窗口已弹出")

    def create_dwm_thumbnail(self, source, dest):
        thumbnail = ctypes.c_void_p()
        res = dwmapi.DwmRegisterThumbnail(dest, source, ctypes.byref(thumbnail))
        if res == 0:
            self.dwm_thumbnail = thumbnail
            self.using_dwm = True
            return True
        return False

    def update_dwm_thumbnail(self):
        if not self.dwm_thumbnail: return
        
        self.embed_frame.update_idletasks()
        w = self.embed_frame.winfo_width()
        h = self.embed_frame.winfo_height()
        
        props = DWM_THUMBNAIL_PROPERTIES()
        props.dwFlags = dwmapi.DWM_TNP_RECTDESTINATION | dwmapi.DWM_TNP_VISIBLE | dwmapi.DWM_TNP_OPACITY
        props.rcDestination = RECT(0, 0, w, h)
        props.opacity = 255
        props.fVisible = True
        
        dwmapi.DwmUpdateThumbnailProperties(self.dwm_thumbnail, ctypes.byref(props))

    def _resize_embedded_window(self, event):
        if not self.embedded_hwnd or self.using_dwm: return
        w = self.embed_frame.winfo_width()
        h = self.embed_frame.winfo_height()
        win32gui.MoveWindow(self.embedded_hwnd, 0, 0, w, h, True)

    def on_mode_change(self):
        mode = self.run_mode.get()
        self.log(f"切换运行模式: {mode}")
        # 这里可以添加模式切换的具体逻辑，如移动窗口到虚拟屏等
        # 暂时保持简单日志记录，具体逻辑在run_script中处理

    def manage_game_process(self, path, title, mode):
        """启动并管理游戏进程"""
        try:
            proc = subprocess.Popen([path])
            self.log(f"正在等待游戏窗口启动: {title}...")
            
            hwnd = 0
            # 轮询查找窗口，最多等待60秒
            for i in range(60):
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    self.log(f"已找到游戏窗口 (耗时 {i}s)")
                    break
                time.sleep(1)
                
            if not hwnd:
                self.log("等待窗口超时", "warning")
                
            return proc, hwnd
        except Exception as e:
            self.log(f"启动游戏失败: {e}", "error")
            return None, 0

    def monitor_resources(self):
        while self.resource_monitoring:
            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            if cpu > 80 or mem > 80:
                self.log(f"资源警告: CPU {cpu}%, MEM {mem}%", "warning")
            time.sleep(10)

    def start_resource_monitoring(self):
        t = threading.Thread(target=self.monitor_resources, daemon=True)
        t.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManager(root)
    root.mainloop()
