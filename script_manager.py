# -*- coding: utf-8 -*-
"""
游戏脚本管理器 - 简化版
用于控制脚本的运行和管理本地脚本
支持图文并茂的日志显示
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk, ImageDraw
import os
import sys
import subprocess
import threading
import time
import queue
import json
import win32gui
import win32con
import win32api
import win32process
import logging
import logging.handlers
from log_formatter import log_formatter
import psutil
import keyboard

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
        self.root.title("游戏脚本管理器")
        self.root.geometry("1000x700")
        self.root.minsize(800, 500)
        
        self.scripts = []
        self.running_scripts = {}
        self.log_queue = queue.Queue()
        
        self.log_images = []
        
        self.venv_python = self._get_venv_python()
        self.log(f"🚀 启动管理器")
        self.log(f"📌 Python路径: {self.venv_python}")
        
        self.is_paused = False
        self.pause_hotkey = "f9"
        self.current_script_process = None
        self.current_running_script = None
        self.auto_minimize = tk.BooleanVar(value=False)
        self.game_title_var = tk.StringVar()
        self.game_path_var = tk.StringVar()
        self.hotkey_var = tk.StringVar(value=self.pause_hotkey)
        
        # AI 配置变量
        self.ai_api_key_var = tk.StringVar()
        self.ai_endpoint_var = tk.StringVar()
        self.ai_model_var = tk.StringVar(value="Doubao-1.8-Pro")
        
        self.setup_styles()
        self.create_widgets()
        self.load_scripts()
        self.load_config()
        self.update_logs()
        self.check_environment()
        self.register_pause_hotkey()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        self.colors = {
            'bg_dark': '#2b2b2b',
            'bg_light': '#f0f0f0',
            'fg_dark': '#ffffff',
            'fg_light': '#000000',
            'accent': '#007acc',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545',
            'sidebar_bg': '#ffffff',
            'log_bg': '#1e1e1e',
            'log_fg': '#d4d4d4',
            'card_bg': '#ffffff'
        }
        
        self.is_dark_mode = False
        
        # Treeview Styles
        style.configure("Treeview", 
            background="white",
            foreground="#333333",
            rowheight=30,
            fieldbackground="white",
            borderwidth=0,
            font=('微软雅黑', 10)
        )
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        style.map('Treeview', background=[('selected', '#e1f0fa')], foreground=[('selected', '#000000')])
        
        # Button Styles
        style.configure("TButton", font=('微软雅黑', 9))
        style.configure("Action.TButton", font=('微软雅黑', 10), padding=5)
        style.configure("Primary.TButton", font=('微软雅黑', 11, 'bold'), foreground=self.colors['accent'], padding=8)
        style.configure("Danger.TButton", font=('微软雅黑', 11, 'bold'), foreground=self.colors['error'], padding=8)
        style.configure("Icon.TButton", font=('Segoe UI Emoji', 12), padding=2, width=3)
        
        # Frame Styles
        style.configure("Card.TFrame", background=self.colors['card_bg'], relief="flat")
        style.configure("Sidebar.TFrame", background=self.colors['sidebar_bg'])
        style.configure("Main.TFrame", background="#f0f2f5")
        
        # Label Styles
        style.configure("Header.TLabel", font=('微软雅黑', 14, 'bold'), background="#ffffff")
        style.configure("SidebarHeader.TLabel", font=('微软雅黑', 12, 'bold'), background=self.colors['sidebar_bg'], foreground="#333333")
        style.configure("Status.TLabel", font=('微软雅黑', 9), background="#ffffff")
    
    def create_widgets(self):
        # Main Container
        main_container = ttk.Frame(self.root, style="Main.TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top Navigation Bar
        self.create_top_nav(main_container)
        
        # Content Area (Sidebar + Main)
        content_area = ttk.Frame(main_container, style="Main.TFrame")
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # Left Sidebar
        self.create_sidebar(content_area)
        
        # Right Main Panel
        self.create_main_panel(content_area)
        
        self._configure_log_tags()

    def create_top_nav(self, parent):
        nav_bar = ttk.Frame(parent, style="Card.TFrame", padding=(15, 10))
        nav_bar.pack(fill=tk.X, side=tk.TOP)
        
        # App Title
        ttk.Label(nav_bar, text="🎮 游戏脚本管理器", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Status Indicator (Integrated into Top Bar)
        self.status_indicator = ttk.Label(nav_bar, text="● 系统就绪", foreground="green", style="Status.TLabel")
        self.status_indicator.pack(side=tk.LEFT, padx=20)
        
        # Settings Button
        ttk.Button(nav_bar, text="⚙️ 设置", style="Action.TButton", command=self.open_settings_dialog).pack(side=tk.RIGHT)

    def create_sidebar(self, parent):
        sidebar = ttk.Frame(parent, width=300, style="Sidebar.TFrame", padding=10)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False) # Fixed width
        
        # Script List Header
        ttk.Label(sidebar, text="脚本列表", style="SidebarHeader.TLabel").pack(fill=tk.X, pady=(0, 10))
        
        # Script List
        list_frame = ttk.Frame(sidebar, style="Sidebar.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("name",)
        self.script_tree = ttk.Treeview(list_frame, columns=columns, show="tree", selectmode="browse")
        self.script_tree.column("#0", width=0, stretch=tk.NO)
        self.script_tree.column("name", width=280)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.script_tree.yview)
        self.script_tree.configure(yscroll=scrollbar.set)
        
        self.script_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control Panel (Bottom of Sidebar)
        control_panel = ttk.Frame(sidebar, style="Sidebar.TFrame", padding=(0, 20, 0, 0))
        control_panel.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Primary Actions
        ttk.Button(control_panel, text="▶ 运行脚本", command=self.run_script, style="Primary.TButton").pack(fill=tk.X, pady=5)
        
        action_row = ttk.Frame(control_panel, style="Sidebar.TFrame")
        action_row.pack(fill=tk.X, pady=5)
        
        self.pause_btn = ttk.Button(action_row, text="⏸ 暂停", command=self.toggle_pause_ui, style="Action.TButton")
        self.pause_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        ttk.Button(action_row, text="⏹ 停止", command=self.stop_script, style="Danger.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # Secondary Actions
        tools_row = ttk.Frame(control_panel, style="Sidebar.TFrame")
        tools_row.pack(fill=tk.X, pady=10)
        
        ttk.Button(tools_row, text="🔄 刷新", command=self.refresh_scripts, style="Action.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        ttk.Button(tools_row, text="➕ 添加", command=self.add_script, style="Action.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

    def create_main_panel(self, parent):
        main_panel = ttk.Frame(parent, style="Main.TFrame", padding=10)
        main_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Log Viewer Container
        log_container = ttk.Frame(main_panel, style="Card.TFrame", padding=1) # Thin border effect
        log_container.pack(fill=tk.BOTH, expand=True)
        
        # Log Viewer
        self.log_text = tk.Text(log_container, 
            font=("Consolas", 10), 
            state=tk.DISABLED, 
            wrap=tk.WORD,
            bg=self.colors['log_bg'],
            fg=self.colors['log_fg'],
            insertbackground="white",
            selectbackground="#264f78",
            relief="flat",
            padx=10,
            pady=10
        )
        log_scroll = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscroll=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("设置")
        dialog.geometry("600x600")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        container = ttk.Frame(dialog, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Game Configuration
        ttk.Label(container, text="游戏配置", font=('微软雅黑', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(container, text="游戏窗口标题:").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=self.game_title_var).pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(container, text="游戏可执行文件路径:").pack(anchor=tk.W)
        path_frame = ttk.Frame(container)
        path_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Entry(path_frame, textvariable=self.game_path_var).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="📂", width=3, command=self.browse_game_path).pack(side=tk.LEFT, padx=(5, 0))
        
        # Hotkey Configuration
        ttk.Label(container, text="热键设置", font=('微软雅黑', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        hotkey_frame = ttk.Frame(container)
        hotkey_frame.pack(fill=tk.X, pady=(5, 15))
        
        ttk.Label(hotkey_frame, text="暂停/恢复热键:").pack(side=tk.LEFT)
        self.hotkey_entry = ttk.Entry(hotkey_frame, width=10, textvariable=self.hotkey_var)
        self.hotkey_entry.pack(side=tk.LEFT, padx=10)
        ttk.Button(hotkey_frame, text="应用", command=self.set_pause_hotkey).pack(side=tk.LEFT)
        
        # AI Configuration
        ttk.Label(container, text="AI 配置 (豆包视觉模型)", font=('微软雅黑', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        
        ttk.Label(container, text="火山引擎 API Key:").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=self.ai_api_key_var, show="*").pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(container, text="模型端点 ID (Endpoint ID):").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=self.ai_endpoint_var).pack(fill=tk.X, pady=(5, 10))
        
        ttk.Label(container, text="模型名称:").pack(anchor=tk.W)
        ttk.Entry(container, textvariable=self.ai_model_var).pack(fill=tk.X, pady=(5, 15))
        
        # Test Connection Button
        test_frame = ttk.Frame(container)
        test_frame.pack(fill=tk.X, pady=(5, 15))
        ttk.Button(test_frame, text="🔗 测试 AI 连接", command=self.test_ai_connection).pack(fill=tk.X)
        
        # Other Settings
        ttk.Label(container, text="其他设置", font=('微软雅黑', 11, 'bold')).pack(anchor=tk.W, pady=(0, 10))
        ttk.Checkbutton(container, text="运行脚本后自动最小化管理器", variable=self.auto_minimize).pack(anchor=tk.W)
        
        # Close Button
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(btn_frame, text="保存", command=lambda: self.save_settings(dialog)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def _configure_log_tags(self):
        self.log_text.tag_config("timestamp", foreground="#666666", font=("Consolas", 9))
        self.log_text.tag_config("SEARCHING", foreground="#4ec9b0", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("SUCCESS", foreground="#4caf50", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("ERROR", foreground="#f44336", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("WARNING", foreground="#ff9800", font=("微软雅黑", 10))
        self.log_text.tag_config("INFO", foreground="#d4d4d4", font=("微软雅黑", 10))
        self.log_text.tag_config("AI_THINKING", foreground="#9b59b6", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("AI_ACTION", foreground="#e67e22", font=("微软雅黑", 10, "bold"))

    def log(self, message, level="info"):
        self.log_queue.put((message, level, None))
        if level == "debug": logger.debug(message)
        elif level == "warning": logger.warning(message)
        elif level == "error": logger.error(message)
        else: logger.info(message)

    def append_rich_log(self, log_data):
        self.log_text.config(state=tk.NORMAL)
        
        try:
            self.log_text.insert(tk.END, f"[{log_data['timestamp']}] ", "timestamp")
            
            tag = log_data['type']
            self.log_text.insert(tk.END, log_data['text'] + " ", tag)
            
            image_path = log_data.get('image_path')
            if image_path:
                logger.debug(f"尝试加载图片: {image_path}")
                
                if os.path.exists(image_path):
                    try:
                        pil_img = Image.open(image_path)
                        
                        base_height = 30
                        h_percent = (base_height / float(pil_img.size[1]))
                        w_size = int((float(pil_img.size[0]) * float(h_percent)))
                        pil_img = pil_img.resize((w_size, base_height), Image.Resampling.LANCZOS)
                        
                        pil_img = pil_img.convert("L")
                        
                        draw = ImageDraw.Draw(pil_img)
                        w, h = pil_img.size
                        draw.line((0, 0, w, h), fill=128, width=2)
                        draw.rectangle((0, 0, w-1, h-1), outline=128, width=1)
                        
                        tk_img = ImageTk.PhotoImage(pil_img)
                        self.log_images.append(tk_img)
                        
                        self.log_text.insert(tk.END, " ")
                        self.log_text.image_create(tk.END, image=tk_img)
                        self.log_text.insert(tk.END, " ")
                        logger.debug(f"图片加载成功: {image_path}")
                    except Exception as e:
                        logger.error(f"图片加载失败: {e}, 路径: {image_path}")
                        self.log_text.insert(tk.END, f"[图片加载失败: {os.path.basename(image_path)}]", "ERROR")
                else:
                    logger.warning(f"图片文件不存在: {image_path}")
                    self.log_text.insert(tk.END, f"[图片不存在: {os.path.basename(image_path)}]", "WARNING")
            
            self.log_text.insert(tk.END, "\n")
            self.log_text.see(tk.END)
        except Exception as e:
            logger.error(f"日志插入失败: {e}")
        finally:
            self.log_text.config(state=tk.DISABLED)

    def update_logs(self):
        while not self.log_queue.empty():
            item = self.log_queue.get()
            
            if len(item) == 2:
                message, level = item
                log_data = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "type": level.upper(),
                    "text": message,
                    "image_path": None,
                    "raw": message
                }
                self.append_rich_log(log_data)
            elif len(item) == 3:
                message, level, script_dir = item
                parsed = log_formatter.parse_line(message, script_dir)
                if parsed:
                    self.append_rich_log(parsed)
            
            if level == "debug": logger.debug(message)
            elif level == "warning": logger.warning(message)
            elif level == "error": logger.error(message)
            else: logger.info(message)
        
        self.root.after(100, self.update_logs)

    def _get_venv_python(self):
        project_root = os.path.dirname(os.path.abspath(__file__))
        venv_python = os.path.join(project_root, "venv", "Scripts", "python.exe")
        if os.path.exists(venv_python): return venv_python
        if getattr(sys, 'frozen', False): return sys.executable
        return sys.executable

    def check_environment(self):
        self.log("🔍 正在检查运行环境...")
        try:
            subprocess.check_call([self.venv_python, '-c', 'import airtest, win32gui, numpy, cv2'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log("✅ 环境检查通过: 核心依赖已安装")
        except Exception as e:
            self.log(f"⚠️  环境检查警告: {e}", "warning")

    def load_scripts(self):
        self.log("📂 正在加载脚本...")
        self.scripts = []
        project_root = os.path.dirname(os.path.abspath(__file__))
        
        games_dir = os.path.join(project_root, "games")
        test_files_dir = os.path.join(project_root, "test_files")
        
        if os.path.exists(games_dir):
            for root, dirs, files in os.walk(games_dir):
                for f in files:
                    if f.endswith(".py") and not f.startswith("_"):
                        path = os.path.join(root, f)
                        rel_path = os.path.relpath(path, games_dir)
                        parts = rel_path.replace("\\", "/").split("/")
                        if len(parts) >= 2:
                            game_name = parts[0].replace("_script", "").replace("_", " ").title()
                            module_name = parts[1].title()
                            script_name = parts[2].replace(".py", "").title()
                            name = f"{game_name} - {module_name} - {script_name}"
                        else:
                            name = os.path.basename(path).replace(".py", "")
                        
                        self.scripts.append({"name": name, "path": path, "status": "就绪"})
        
        if os.path.exists(test_files_dir):
            for f in os.listdir(test_files_dir):
                if f.endswith(".py") and not f.startswith("_"):
                    path = os.path.join(test_files_dir, f)
                    name = f"测试 - {f.replace('.py', '')}"
                    self.scripts.append({"name": name, "path": path, "status": "就绪"})
        
        for f in os.listdir(project_root):
            if f.endswith(".py") and f.startswith("test_"):
                path = os.path.join(project_root, f)
                name = f"根目录 - {f.replace('.py', '')}"
                self.scripts.append({"name": name, "path": path, "status": "就绪"})
        
        self.log(f"✅ 已加载 {len(self.scripts)} 个脚本")
        self.update_script_tree()

    def update_script_tree(self):
        for item in self.script_tree.get_children():
            self.script_tree.delete(item)
        
        for script in self.scripts:
            self.script_tree.insert("", tk.END, values=(script["name"], script["status"]))

    def run_script(self):
        selected = self.script_tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一个脚本")
            return
            
        item = self.script_tree.item(selected[0])
        script_name = item['values'][0]
        
        script = next((s for s in self.scripts if s["name"] == script_name), None)
        if not script: return
        
        if script["status"] == "运行中":
            messagebox.showinfo("提示", "该脚本已在运行中")
            return

        game_title = self.game_title_var.get()
        game_path = self.game_path_var.get()
        
        game_hwnd = 0
        game_process = None
        
        if game_title:
            game_hwnd = win32gui.FindWindow(None, game_title)
            if game_hwnd == 0 and game_path and os.path.exists(game_path):
                self.log(f"🎮 启动游戏进程: {game_path}")
                game_process, game_hwnd = self.manage_game_process(game_path, game_title)
            elif game_hwnd == 0:
                self.log("⚠️  未找到游戏窗口", "warning")
        
        script["status"] = "运行中"
        self.current_running_script = script
        self.update_script_tree()
        self.status_indicator.config(text=f"● 运行中: {script_name}", foreground="#007acc")
        self.pause_btn.config(text="⏸ 暂停")
        
        self.log(f"🚀 开始执行脚本: {script_name}")
        
        thread = threading.Thread(
            target=self._run_script_in_thread,
            args=(script, game_process, game_hwnd),
            daemon=True
        )
        thread.start()
        
        if self.auto_minimize.get():
            self.root.iconify()

    def _run_script_in_thread(self, script, game_process, game_hwnd):
        try:
            cmd_args = [self.venv_python, script['path']]
            
            if game_hwnd:
                title = win32gui.GetWindowText(game_hwnd)
                cmd_args.extend([
                    f"--window-title={title}",
                    f"--window-hwnd={game_hwnd}"
                ])
                self.log(f"🖥️  目标窗口: {title} (句柄: {game_hwnd})")
            
            self.log(f"📝 执行命令: {' '.join(cmd_args)}")
            
            script_dir = os.path.dirname(script['path'])
            
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
            
            self.current_script_process = psutil.Process(process.pid)
            
            for line in process.stdout:
                self.log_queue.put((line.strip(), "info", script_dir))
            
            process.wait()
            
            if process.returncode == 0:
                self.log(f"✅ 脚本执行成功: {script['name']}", "success")
            else:
                self.log(f"❌ 脚本异常退出 (代码: {process.returncode}): {script['name']}", "error")
                
        except Exception as e:
            self.log(f"❌ 运行错误: {e}", "error")
        finally:
            script["status"] = "就绪"
            self.running_scripts.pop(script['path'], None)
            self.current_script_process = None
            self.current_running_script = None
            self.is_paused = False
            self.root.after(0, self.update_script_tree)
            self.root.after(0, lambda: self.status_indicator.config(text="● 系统就绪", foreground="green"))
            self.root.after(0, lambda: self.pause_btn.config(text="⏸ 暂停"))

    def stop_script(self):
        selected = self.script_tree.selection()
        if not selected: return
        
        item = self.script_tree.item(selected[0])
        script_name = item['values'][0]
        script = next((s for s in self.scripts if s["name"] == script_name), None)
        
        if script and script['path'] in self.running_scripts:
            info = self.running_scripts[script['path']]
            info['process'].terminate()
            script["status"] = "就绪"
            self.is_paused = False
            self.current_script_process = None
            self.current_running_script = None
            self.pause_btn.config(text="⏸ 暂停")
            self.update_script_tree()
            self.log(f"🛑 已停止脚本: {script_name}")
            self.status_indicator.config(text="● 系统就绪", foreground="green")

    def refresh_scripts(self):
        self.load_scripts()
        self.log("🔄 脚本列表已刷新")

    def add_script(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path:
            name = os.path.basename(path).replace(".py", "")
            self.scripts.append({"name": name, "path": path, "status": "就绪"})
            self.update_script_tree()
            self.log(f"➕ 已添加脚本: {name}")

    def browse_game_path(self):
        path = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if path:
            self.game_path_var.set(path)
            self.log(f"📁 已选择游戏路径: {path}")

    def manage_game_process(self, path, title):
        try:
            proc = subprocess.Popen([path])
            self.log(f"⏳ 正在等待游戏窗口启动: {title}...")
            
            hwnd = 0
            for i in range(60):
                hwnd = win32gui.FindWindow(None, title)
                if hwnd:
                    self.log(f"✅ 已找到游戏窗口 (耗时 {i}秒)")
                    break
                time.sleep(1)
                
            if not hwnd:
                self.log("⚠️  等待窗口超时", "warning")
                
            return proc, hwnd
        except Exception as e:
            self.log(f"❌ 启动游戏失败: {e}", "error")
            return None, 0
    
    def register_pause_hotkey(self):
        """
        注册全局暂停热键
        """
        try:
            keyboard.add_hotkey(self.pause_hotkey, self.toggle_pause)
            self.log(f"🔑 已注册暂停热键: {self.pause_hotkey.upper()}")
            self.log("💡 提示: 如果热键不工作，请尝试以管理员身份运行程序", "info")
        except Exception as e:
            self.log(f"⚠️  注册热键失败: {e}", "warning")
            self.log("💡 提示: 全局热键可能需要管理员权限，请以管理员身份运行", "info")
    
    def set_pause_hotkey(self):
        """
        设置新的暂停热键
        """
        try:
            new_hotkey = self.hotkey_entry.get().strip().lower()
            if not new_hotkey:
                messagebox.showwarning("提示", "请输入热键")
                return
            
            keyboard.unhook_all_hotkeys()
            self.pause_hotkey = new_hotkey
            keyboard.add_hotkey(self.pause_hotkey, self.toggle_pause)
            self.log(f"🔑 热键已更新为: {self.pause_hotkey.upper()}")
            messagebox.showinfo("成功", f"暂停热键已设置为: {self.pause_hotkey.upper()}")
        except Exception as e:
            self.log(f"❌ 设置热键失败: {e}", "error")
            messagebox.showerror("错误", f"设置热键失败: {e}")
    
    def suspend_process_tree(self, pid):
        """
        暂停整个进程树（主进程和所有子进程）
        """
        try:
            parent = psutil.Process(pid)
            for child in parent.children(recursive=True):
                try:
                    child.suspend()
                except psutil.NoSuchProcess:
                    pass
            parent.suspend()
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            logger.error(f"暂停进程树失败: {e}")
            return False
    
    def resume_process_tree(self, pid):
        """
        恢复整个进程树（主进程和所有子进程）
        """
        try:
            parent = psutil.Process(pid)
            parent.resume()
            for child in parent.children(recursive=True):
                try:
                    child.resume()
                except psutil.NoSuchProcess:
                    pass
            return True
        except psutil.NoSuchProcess:
            return False
        except Exception as e:
            logger.error(f"恢复进程树失败: {e}")
            return False
    
    def toggle_pause(self):
        """
        切换暂停/恢复状态（热键调用）
        """
        if not self.current_script_process:
            return
        
        try:
            if self.is_paused:
                if self.resume_process_tree(self.current_script_process.pid):
                    self.is_paused = False
                    self.pause_btn.config(text="⏸ 暂停")
                    if self.current_running_script:
                        self.current_running_script["status"] = "运行中"
                        self.update_script_tree()
                    self.log("▶️ 脚本已恢复运行")
                else:
                    self.log("⚠️  进程已结束，无法恢复", "warning")
            else:
                if self.suspend_process_tree(self.current_script_process.pid):
                    self.is_paused = True
                    self.pause_btn.config(text="▶ 恢复")
                    if self.current_running_script:
                        self.current_running_script["status"] = "已暂停"
                        self.update_script_tree()
                    self.log("⏸️ 脚本已暂停")
                else:
                    self.log("⚠️  进程已结束，无法暂停", "warning")
        except Exception as e:
            self.log(f"❌ 切换暂停状态失败: {e}", "error")
    
    def load_config(self):
        """
        加载配置文件
        """
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot_config.json")
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.game_title_var.set(config.get('last_script', ''))
                    self.game_path_var.set(config.get('last_path', ''))
                    
                    # 加载 AI 配置
                    ai_config = config.get('ai_config', {})
                    self.ai_api_key_var.set(ai_config.get('api_key', ''))
                    self.ai_endpoint_var.set(ai_config.get('endpoint_id', ''))
                    self.ai_model_var.set(ai_config.get('model_name', 'Doubao-1.8-Pro'))
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
    
    def save_settings(self, dialog):
        """
        保存设置并关闭对话框
        """
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot_config.json")
            import json
            config = {
                'last_script': self.game_title_var.get(),
                'last_path': self.game_path_var.get(),
                'last_filename': '',
                'ai_config': {
                    'api_key': self.ai_api_key_var.get(),
                    'endpoint_id': self.ai_endpoint_var.get(),
                    'model_name': self.ai_model_var.get()
                }
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            dialog.destroy()
            self.log("✅ 设置已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def test_ai_connection(self):
        """
        测试 AI 连接
        """
        api_key = self.ai_api_key_var.get()
        endpoint_id = self.ai_endpoint_var.get()
        model_name = self.ai_model_var.get()
        
        if not api_key or not endpoint_id:
            messagebox.showwarning("提示", "请先填写 API Key 和 Endpoint ID")
            return
        
        try:
            from ai_brain import DoubaoBrain
            
            # 创建测试大脑
            brain = DoubaoBrain(api_key=api_key, endpoint_id=endpoint_id, model_name=model_name)
            
            # 测试连接
            self.log("🔗 正在测试 AI 连接...")
            if brain.test_connection():
                messagebox.showinfo("成功", "AI 连接测试成功！")
                self.log("✅ AI 连接测试成功")
            else:
                messagebox.showerror("失败", "AI 连接测试失败，请检查 API Key 和 Endpoint ID")
                self.log("❌ AI 连接测试失败", "error")
        except ImportError:
            messagebox.showerror("错误", "未找到 ai_brain 模块，请确保已安装 openai 库")
            self.log("❌ 未找到 ai_brain 模块", "error")
        except Exception as e:
            messagebox.showerror("错误", f"测试连接时出错: {e}")
            self.log(f"❌ 测试连接错误: {e}", "error")
    
    def toggle_pause_ui(self):
        """
        切换暂停/恢复状态（UI按钮调用）
        """
        if not self.current_script_process:
            messagebox.showinfo("提示", "没有正在运行的脚本")
            return
        
        self.toggle_pause()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManager(root)
    root.mainloop()
