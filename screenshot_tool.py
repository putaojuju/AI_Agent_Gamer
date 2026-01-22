# -*- coding: utf-8 -*-
"""
游戏脚本截图工具
用于便捷截取编写识图脚本所需的截图，并自动保存到脚本对应的根目录下
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import time
import json
import ctypes
from mss import mss
from PIL import Image, ImageTk, ImageDraw
import win32gui
import win32con
import win32api
import threading
import pyperclip
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

# DPI 适配（关键！）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot_config.json")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshot_history.json")

# 游戏脚本目录
GAMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "games")

# 虚拟屏分辨率
VIRTUAL_SCREEN_WIDTH = 1920
VIRTUAL_SCREEN_HEIGHT = 1080


class ScreenshotTool:
    """
    截图工具主类
    """

    def __init__(self):
        """
        初始化截图工具
        """
        # 使用 TkinterDnD 初始化主窗口
        if HAS_DND:
            self.root = TkinterDnD.Tk()
        else:
            self.root = tk.Tk()
            
        self.root.title("游戏脚本截图工具 v1.1")
        self.root.geometry("1100x800")
        self.root.minsize(900, 700)

        # 设置主题
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 自定义样式
        self.style.configure("TButton", padding=5)
        self.style.configure("TLabelFrame", font=("Arial", 9, "bold"))

        # 当前截图
        self.current_screenshot = None
        self.current_screenshot_path = None

        # 当前游戏脚本路径
        self.current_script_path = None

        # 截图模式
        self.capture_mode = tk.StringVar(value="region")

        # 游戏脚本选择
        self.game_script_var = tk.StringVar()

        # 文件名
        self.filename_var = tk.StringVar()

        # 保存路径
        self.save_path_var = tk.StringVar()

        # 灰度预览
        self.show_grayscale = tk.BooleanVar(value=False)

        # 二值化预览
        self.show_binary = tk.BooleanVar(value=False)

        # 二值化阈值
        self.binary_threshold = tk.IntVar(value=127)

        # 代码片段
        self.code_var = tk.StringVar()

        # 历史记录
        self.history = []

        # 区域选择状态
        self.selecting_region = False
        self.region_start = None
        self.region_end = None
        self.region_overlay = None

        # 区域选择窗口
        self.region_window = None
        self.region_canvas = None

        # --- 图片编辑状态 ---
        self.edit_history = []  # 撤销栈
        self.preview_scale = 1.0
        self.preview_offset = (0, 0)
        
        # 裁剪状态
        self.is_cropping = False
        self.crop_start = None
        self.crop_rect_id = None
        
        # 魔棒去背景状态
        self.is_magic_wanding = False
        self.magic_wand_start = None
        self.magic_wand_rect_id = None
        self.magic_wand_tolerance = 30  # 颜色容差

        # 加载配置和历史记录
        self.load_config()
        self.load_history()

        # 创建UI
        self.create_widgets()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 设置拖拽支持
        self.setup_drag_drop()

    def setup_drag_drop(self):
        """
        设置拖拽支持
        """
        if HAS_DND:
            try:
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.on_drop_file)
            except Exception as e:
                print(f"拖拽功能初始化失败: {e}")
        else:
            print("未安装 tkinterdnd2 模块，拖拽功能不可用")

    def on_drop_file(self, event):
        """
        处理拖拽文件
        """
        try:
            filepath = event.data
            
            # 清洗路径 (tkinterdnd2 在路径有空格时会包裹 {})
            if filepath.startswith('{') and filepath.endswith('}'):
                filepath = filepath[1:-1]
            
            # 处理多个文件（只取第一个）
            if '\n' in filepath:
                filepath = filepath.split('\n')[0]
            
            if os.path.isfile(filepath) and filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
                self.load_image_from_file(filepath)
            else:
                messagebox.showwarning("警告", "不支持的文件格式")
        except Exception as e:
            print(f"处理拖拽文件失败: {e}")

    def create_widgets(self):
        """
        创建GUI组件
        """
        # 主分割窗格
        self.paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧控制栏
        self.sidebar = ttk.Frame(self.paned_window, width=320, padding="5")
        self.paned_window.add(self.sidebar, weight=0)

        # 右侧预览区
        self.preview_frame = ttk.Frame(self.paned_window, padding="5")
        self.paned_window.add(self.preview_frame, weight=1)

        # --- 左侧组件 ---
        self.create_script_selection(self.sidebar)
        self.create_capture_mode_selection(self.sidebar)
        self.create_capture_control(self.sidebar)
        self.create_save_area(self.sidebar)
        self.create_code_area(self.sidebar)

        # --- 右侧组件 ---
        self.create_preview_area(self.preview_frame)

    def create_script_selection(self, parent):
        """
        创建游戏脚本选择区
        """
        script_frame = ttk.LabelFrame(parent, text="1. 脚本选择", padding="5")
        script_frame.pack(fill=tk.X, pady=5)

        # 游戏脚本下拉菜单
        ttk.Label(script_frame, text="选择脚本:").pack(anchor=tk.W, padx=5)
        
        input_frame = ttk.Frame(script_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=2)

        script_combo = ttk.Combobox(
            input_frame,
            textvariable=self.game_script_var,
            state="readonly"
        )
        script_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 刷新按钮
        ttk.Button(input_frame, text="↻", width=3, command=lambda: self.load_game_scripts(script_combo)).pack(side=tk.LEFT, padx=(5, 0))

        # 加载游戏脚本列表
        self.load_game_scripts(script_combo)

        # 绑定选择事件
        script_combo.bind("<<ComboboxSelected>>", self.on_script_selected)

    def create_capture_mode_selection(self, parent):
        """
        创建截图模式选择区
        """
        mode_frame = ttk.LabelFrame(parent, text="2. 截图模式", padding="5")
        mode_frame.pack(fill=tk.X, pady=5)

        # 全屏截图
        ttk.Radiobutton(
            mode_frame,
            text="全屏截图",
            variable=self.capture_mode,
            value="fullscreen"
        ).pack(anchor=tk.W, padx=5, pady=2)

        # 窗口截图
        ttk.Radiobutton(
            mode_frame,
            text="窗口截图（吸附游戏窗口）",
            variable=self.capture_mode,
            value="window"
        ).pack(anchor=tk.W, padx=5, pady=2)

        # 自定义区域截图
        ttk.Radiobutton(
            mode_frame,
            text="自定义区域（拖拽选择）",
            variable=self.capture_mode,
            value="region"
        ).pack(anchor=tk.W, padx=5, pady=2)

    def create_capture_control(self, parent):
        """
        创建截图控制区
        """
        control_frame = ttk.LabelFrame(parent, text="3. 截图控制", padding="5")
        control_frame.pack(fill=tk.X, pady=5)

        # 按钮区域
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        # 截图按钮
        capture_btn = ttk.Button(
            btn_frame,
            text="截图 (Enter)",
            command=self.capture_screenshot,
            width=12
        )
        capture_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 重新截图按钮
        recapture_btn = ttk.Button(
            btn_frame,
            text="重新截图",
            command=self.recapture_screenshot,
            width=12
        )
        recapture_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 加载图片按钮
        load_btn = ttk.Button(
            btn_frame,
            text="加载图片",
            command=self.load_image,
            width=12
        )
        load_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # 绑定快捷键
        self.root.bind('<Return>', lambda e: self.capture_screenshot())

        # 分隔线
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # 图像处理选项
        ttk.Label(control_frame, text="图像预览处理:").pack(anchor=tk.W, padx=5)

        # 灰度预览复选框
        grayscale_check = ttk.Checkbutton(
            control_frame,
            text="灰度预览",
            variable=self.show_grayscale,
            command=self.update_preview
        )
        grayscale_check.pack(anchor=tk.W, padx=10, pady=2)

        # 二值化预览复选框
        binary_check = ttk.Checkbutton(
            control_frame,
            text="二值化预览",
            variable=self.show_binary,
            command=self.update_preview
        )
        binary_check.pack(anchor=tk.W, padx=10, pady=2)

        # 二值化阈值滑块区域
        threshold_frame = ttk.Frame(control_frame)
        threshold_frame.pack(fill=tk.X, padx=10, pady=2)
        
        # 阈值说明和数值显示
        label_frame = ttk.Frame(threshold_frame)
        label_frame.pack(fill=tk.X)
        ttk.Label(label_frame, text="二值化阈值:").pack(side=tk.LEFT)
        self.threshold_value_label = ttk.Label(label_frame, text=f"{self.binary_threshold.get()}")
        self.threshold_value_label.pack(side=tk.RIGHT)

        def on_threshold_change(val):
            self.threshold_value_label.config(text=f"{int(float(val))}")
            self.update_preview()

        threshold_scale = ttk.Scale(
            threshold_frame,
            from_=0,
            to=255,
            variable=self.binary_threshold,
            orient=tk.HORIZONTAL,
            command=on_threshold_change
        )
        threshold_scale.pack(fill=tk.X, pady=(2, 0))

        # 应用效果按钮
        ttk.Button(
            control_frame,
            text="应用当前效果",
            command=self.apply_effect
        ).pack(fill=tk.X, padx=10, pady=5)

    def create_preview_area(self, parent):
        """
        创建预览区
        """
        preview_frame = ttk.LabelFrame(parent, text="预览", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 工具栏
        toolbar = ttk.Frame(preview_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(toolbar, text="裁剪", width=8, command=self.start_crop).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="撤销", width=8, command=self.undo_edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="魔棒去底", width=10, command=self.start_magic_wand).pack(side=tk.LEFT, padx=2)
        ttk.Label(toolbar, text="(双击确认裁剪，右键取消)").pack(side=tk.LEFT, padx=5)

        # 预览画布框架
        canvas_frame = ttk.Frame(preview_frame, relief=tk.SUNKEN, borderwidth=1)
        canvas_frame.pack(fill=tk.BOTH, expand=True)

        # 创建画布
        self.preview_canvas = tk.Canvas(canvas_frame, bg="#2b2b2b")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定画布事件
        self.preview_canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.preview_canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.preview_canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.preview_canvas.bind("<Button-3>", self.on_canvas_right_click)

        # 初始化预览图像
        self.preview_image = None
        self.preview_image_grayscale = None
        self.preview_image_binary = None

        # 显示提示信息
        self.preview_canvas.create_text(
            300, 200,
            text="点击'截图'按钮或按 Enter 开始截图",
            fill="#888888",
            font=("Arial", 14)
        )

    def create_save_area(self, parent):
        """
        创建命名和保存区
        """
        save_frame = ttk.LabelFrame(parent, text="4. 保存设置", padding="5")
        save_frame.pack(fill=tk.X, pady=5)

        # 文件名输入
        ttk.Label(save_frame, text="文件名:").pack(anchor=tk.W, padx=5)
        
        filename_frame = ttk.Frame(save_frame)
        filename_frame.pack(fill=tk.X, padx=5, pady=2)
        
        filename_entry = ttk.Entry(filename_frame, textvariable=self.filename_var)
        filename_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(filename_frame, text=".png").pack(side=tk.LEFT)

        # 历史记录下拉菜单
        ttk.Label(save_frame, text="历史记录:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        history_combo = ttk.Combobox(
            save_frame,
            textvariable=tk.StringVar(),
            state="readonly"
        )
        history_combo.pack(fill=tk.X, padx=5, pady=2)

        # 加载历史记录
        self.load_history_combo(history_combo)

        # 绑定选择事件
        history_combo.bind("<<ComboboxSelected>>", self.on_history_selected)

        # 保存路径显示
        ttk.Label(save_frame, text="保存路径:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        path_frame = ttk.Frame(save_frame)
        path_frame.pack(fill=tk.X, padx=5, pady=2)
        
        path_entry = ttk.Entry(path_frame, textvariable=self.save_path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 浏览按钮
        ttk.Button(path_frame, text="...", width=3, command=self.browse_save_path).pack(side=tk.LEFT, padx=(5, 0))

        # 保存按钮
        ttk.Button(save_frame, text="保存截图", command=self.save_screenshot).pack(fill=tk.X, padx=5, pady=10)

    def create_code_area(self, parent):
        """
        创建代码生成区
        """
        code_frame = ttk.LabelFrame(parent, text="5. Airtest 代码", padding="5")
        code_frame.pack(fill=tk.BOTH, expand=True, pady=5)  # 允许垂直扩展

        # 文本框容器（用于放置滚动条）
        text_container = ttk.Frame(code_frame)
        text_container.pack(fill=tk.BOTH, expand=True, pady=5)

        # 滚动条
        scrollbar = ttk.Scrollbar(text_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 代码文本框
        self.code_text = tk.Text(
            text_container,
            height=5,
            width=30,
            font=("Consolas", 9),
            yscrollcommand=scrollbar.set,
            undo=True  # 启用撤销
        )
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定滚动条
        scrollbar.config(command=self.code_text.yview)
        
        self.code_text.insert(tk.END, "等待截图...")
        self.code_text.config(state=tk.DISABLED)

        # 复制按钮
        ttk.Button(code_frame, text="复制到剪贴板", command=self.copy_code).pack(fill=tk.X, padx=5, pady=(0, 5))

    def load_game_scripts(self, combo):
        """
        加载游戏脚本列表
        """
        scripts = []

        # 遍历 games 目录
        if os.path.exists(GAMES_DIR):
            for game_name in os.listdir(GAMES_DIR):
                game_path = os.path.join(GAMES_DIR, game_name)
                if os.path.isdir(game_path):
                    # 遍历游戏脚本目录
                    for script_name in os.listdir(game_path):
                        script_path = os.path.join(game_path, script_name)
                        if os.path.isdir(script_path):
                            # 添加到列表
                            scripts.append(f"{game_name}/{script_name}")

        # 更新下拉菜单
        combo['values'] = scripts
        if scripts:
            combo.current(0)
            self.on_script_selected(None)

    def on_script_selected(self, event):
        """
        脚本选择事件处理
        """
        script_name = self.game_script_var.get()
        if script_name:
            # 设置保存路径
            self.current_script_path = os.path.join(GAMES_DIR, script_name)
            self.save_path_var.set(self.current_script_path)

    def load_config(self):
        """
        加载配置文件
        """
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.game_script_var.set(config.get('last_script', ''))
                    self.save_path_var.set(config.get('last_path', ''))
                    self.filename_var.set(config.get('last_filename', ''))
        except Exception as e:
            print(f"加载配置文件失败: {e}")

    def save_config(self):
        """
        保存配置文件
        """
        try:
            config = {
                'last_script': self.game_script_var.get(),
                'last_path': self.save_path_var.get(),
                'last_filename': self.filename_var.get()
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def load_history(self):
        """
        加载历史记录
        """
        try:
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")

    def save_history(self, filename):
        """
        保存历史记录
        """
        try:
            # 添加到历史记录
            if filename not in self.history:
                self.history.insert(0, filename)
                # 只保留最近 20 条
                self.history = self.history[:20]

            # 保存到文件
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def load_history_combo(self, combo):
        """
        加载历史记录到下拉菜单
        """
        combo['values'] = self.history

    def on_history_selected(self, event):
        """
        历史记录选择事件处理
        """
        combo = event.widget
        filename = combo.get()
        if filename:
            self.filename_var.set(filename)

    def browse_save_path(self):
        """
        浏览保存路径
        """
        path = filedialog.askdirectory(title="选择保存路径")
        if path:
            self.save_path_var.set(path)

    def capture_screenshot(self):
        """
        截图（关键：隐藏窗口防止遮挡）
        """
        mode = self.capture_mode.get()

        if mode == "region":
            # 自定义区域截图模式
            self.start_region_selection()
        else:
            # 全屏或窗口截图模式
            # 隐藏工具窗口
            self.root.withdraw()
            time.sleep(0.2)  # 等待窗口完全隐藏

            try:
                # 执行截图
                self._do_capture()
            except Exception as e:
                messagebox.showerror("错误", f"截图失败: {e}")
            finally:
                # 恢复工具窗口
                self.root.deiconify()
                self.root.lift()  # 确保窗口在最前面
                self.root.focus_force()

    def recapture_screenshot(self):
        """
        重新截图
        """
        self.capture_screenshot()

    def load_image(self):
        """
        加载图片文件
        """
        filepath = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp"), ("All files", "*.*")]
        )
        if filepath:
            self.load_image_from_file(filepath)

    def load_image_from_file(self, filepath):
        """
        从文件加载图片
        """
        try:
            image = Image.open(filepath)
            # 转换为 RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            self.current_screenshot = image
            self.current_screenshot_path = filepath
            
            # 更新文件名和路径
            dirname, filename = os.path.split(filepath)
            name, ext = os.path.splitext(filename)
            
            self.filename_var.set(name)
            self.save_path_var.set(dirname)
            
            # 清空撤销栈
            self.edit_history = []
            
            # 更新预览
            self.update_preview()
            self.generate_code()
            
            # 提示
            if not HAS_DND:
                print("提示: 安装 tkinterdnd2 模块可支持拖拽加载图片 (pip install tkinterdnd2)")
                  
        except Exception as e:
            messagebox.showerror("错误", f"加载图片失败: {e}")

    def start_region_selection(self):
        """
        启动区域选择
        """
        # 隐藏工具窗口
        self.root.withdraw()
        time.sleep(0.2)

        # 创建全屏透明窗口用于区域选择
        self.region_window = tk.Toplevel()
        self.region_window.attributes('-fullscreen', True)
        self.region_window.attributes('-alpha', 0.3)
        self.region_window.attributes('-topmost', True)
        self.region_window.configure(bg='black')
        self.region_window.overrideredirect(True)  # 无边框

        # 创建画布
        self.region_canvas = tk.Canvas(self.region_window, bg='black', highlightthickness=0)
        self.region_canvas.pack(fill=tk.BOTH, expand=True)

        # 绑定鼠标事件
        self.region_canvas.bind('<ButtonPress-1>', self.on_region_start)
        self.region_canvas.bind('<B1-Motion>', self.on_region_drag)
        self.region_canvas.bind('<ButtonRelease-1>', self.on_region_end)
        self.region_canvas.bind('<Escape>', self.on_region_cancel)

        # 显示提示
        self.region_canvas.create_text(
            self.region_window.winfo_screenwidth() // 2,
            50,
            text="拖拽鼠标选择截图区域，按 ESC 取消",
            fill='white',
            font=('Arial', 14)
        )

        # 等待窗口显示
        self.region_window.update()

    def on_region_start(self, event):
        """
        区域选择开始
        """
        self.region_start = (event.x, event.y)
        self.region_end = (event.x, event.y)
        self.selecting_region = True

    def on_region_drag(self, event):
        """
        区域选择拖拽
        """
        if self.selecting_region:
            self.region_end = (event.x, event.y)

            # 清除之前的矩形
            self.region_canvas.delete('selection')

            # 绘制选择矩形
            x1, y1 = self.region_start
            x2, y2 = self.region_end
            self.region_canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='red',
                width=2,
                tags='selection'
            )

            # 显示尺寸信息
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            self.region_canvas.delete('size_info')
            self.region_canvas.create_text(
                (x1 + x2) // 2,
                y1 - 20,
                text=f"{width} x {height}",
                fill='white',
                font=('Arial', 12),
                tags='size_info'
            )

    def on_region_end(self, event):
        """
        区域选择结束
        """
        if self.selecting_region:
            self.selecting_region = False

            # 关闭区域选择窗口
            self.region_window.destroy()
            self.region_window = None
            self.region_canvas = None

            # 执行截图
            try:
                self._do_capture_region()
            except Exception as e:
                messagebox.showerror("错误", f"截图失败: {e}")
            finally:
                # 恢复工具窗口
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()

    def on_region_cancel(self, event):
        """
        取消区域选择
        """
        self.selecting_region = False

        # 关闭区域选择窗口
        if self.region_window:
            self.region_window.destroy()
            self.region_window = None
            self.region_canvas = None

        # 恢复工具窗口
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _do_capture(self):
        """
        执行截图（内部方法）
        """
        mode = self.capture_mode.get()

        with mss() as sct:
            if mode == "fullscreen":
                # 全屏截图
                monitor = sct.monitors[0]  # 主显示器
                screenshot = sct.grab(monitor)

            elif mode == "window":
                # 窗口截图
                script_name = self.game_script_var.get()
                if not script_name:
                    messagebox.showwarning("警告", "请先选择游戏脚本")
                    return

                # 从脚本名提取游戏标题（简化处理）
                game_title = script_name.split('/')[0]

                # 查找游戏窗口（使用更精确的方法）
                hwnd = self.find_game_window(game_title)
                if not hwnd:
                    messagebox.showwarning("警告", f"未找到游戏窗口: {game_title}")
                    return

                # 获取窗口位置和大小
                rect = win32gui.GetWindowRect(hwnd)
                monitor = {
                    "left": rect[0],
                    "top": rect[1],
                    "width": rect[2] - rect[0],
                    "height": rect[3] - rect[1]
                }
                screenshot = sct.grab(monitor)

            # 转换为 PIL 图像
            self.current_screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # 更新预览
            self.update_preview()

            # 生成代码片段
            self.generate_code()

    def _do_capture_region(self):
        """
        执行区域截图
        """
        if not self.region_start or not self.region_end:
            messagebox.showwarning("警告", "请先选择区域")
            return

        # 计算区域坐标
        x1, y1 = self.region_start
        x2, y2 = self.region_end

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        # 使用 mss 截图
        with mss() as sct:
            monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }
            screenshot = sct.grab(monitor)

            # 转换为 PIL 图像
            self.current_screenshot = Image.frombytes('RGB', screenshot.size, screenshot.rgb)

            # 更新预览
            self.update_preview()

            # 生成代码片段
            self.generate_code()

    def find_game_window(self, game_title):
        """
        查找游戏窗口
        """
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and game_title.lower() in title.lower():
                    windows.append(hwnd)
            return True

        windows = []
        win32gui.EnumWindows(callback, windows)

        # 返回第一个匹配的窗口
        return windows[0] if windows else None

    def update_preview(self):
        """
        更新预览区
        """
        if not self.current_screenshot:
            return

        # 根据预览模式处理图像
        if self.show_binary.get():
            # 二值化预览
            preview_image = self._convert_to_binary(self.current_screenshot, self.binary_threshold.get())
        elif self.show_grayscale.get():
            # 灰度预览
            preview_image = self._convert_to_grayscale(self.current_screenshot)
        else:
            # 原始图像
            preview_image = self.current_screenshot

        # 调整图像大小以适应画布
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width > 0 and canvas_height > 0:
            # 计算缩放比例
            img_width, img_height = preview_image.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            # 记录缩放比例和偏移量（用于坐标转换）
            self.preview_scale = scale
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)

            # 缩放图像
            preview_image = preview_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 转换为 Tkinter 图像
            self.preview_image = ImageTk.PhotoImage(preview_image)

            # 清除画布
            self.preview_canvas.delete("all")

            # 计算居中位置
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            
            self.preview_offset = (x, y)

            # 显示图像
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image)

            # 显示图像信息
            if self.current_screenshot_path and os.path.exists(self.current_screenshot_path):
                info_text = f"尺寸: {img_width}x{img_height} | 文件大小: {os.path.getsize(self.current_screenshot_path) / 1024:.1f} KB"
            else:
                info_text = f"尺寸: {img_width}x{img_height}"

            self.preview_canvas.create_text(
                10, 10,
                text=info_text,
                fill="#ffffff",
                anchor=tk.NW,
                font=("Arial", 9)
            )

    def push_undo(self):
        """
        将当前状态压入撤销栈
        """
        if self.current_screenshot:
            self.edit_history.append(self.current_screenshot.copy())
            # 限制撤销栈大小
            if len(self.edit_history) > 10:
                self.edit_history.pop(0)

    def undo_edit(self):
        """
        撤销上一步编辑
        """
        if self.edit_history:
            self.current_screenshot = self.edit_history.pop()
            self.update_preview()
            self.generate_code()
        else:
            messagebox.showinfo("提示", "没有可撤销的操作")

    def apply_effect(self):
        """
        应用当前预览效果到原图
        """
        if not self.current_screenshot:
            return

        if not (self.show_binary.get() or self.show_grayscale.get()):
            messagebox.showinfo("提示", "当前没有启用任何预览效果")
            return

        self.push_undo()

        if self.show_binary.get():
            self.current_screenshot = self._convert_to_binary(self.current_screenshot, self.binary_threshold.get())
            # 应用后通常转为 RGB 以保持兼容性（虽然二值图是单通道，但为了后续处理方便）
            self.current_screenshot = self.current_screenshot.convert("RGB")
            self.show_binary.set(False)
        elif self.show_grayscale.get():
            self.current_screenshot = self._convert_to_grayscale(self.current_screenshot)
            self.current_screenshot = self.current_screenshot.convert("RGB")
            self.show_grayscale.set(False)
        
        self.update_preview()
        messagebox.showinfo("成功", "效果已应用")

    def start_crop(self):
        """
        进入裁剪模式
        """
        if not self.current_screenshot:
            return
        
        self.is_cropping = True
        self.preview_canvas.config(cursor="cross")
        messagebox.showinfo("提示", "请在预览区拖拽鼠标选择裁剪区域，双击选区确认裁剪，右键取消")

    def on_canvas_press(self, event):
        """
        画布鼠标按下事件
        """
        if self.is_cropping:
            self.crop_start = (event.x, event.y)
            if self.crop_rect_id:
                self.preview_canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None

    def on_canvas_drag(self, event):
        """
        画布鼠标拖拽事件
        """
        if self.is_cropping and self.crop_start:
            if self.crop_rect_id:
                self.preview_canvas.delete(self.crop_rect_id)
            
            x1, y1 = self.crop_start
            x2, y2 = event.x, event.y
            
            self.crop_rect_id = self.preview_canvas.create_rectangle(
                x1, y1, x2, y2,
                outline="red",
                width=2,
                dash=(5, 5)
            )

    def on_canvas_release(self, event):
        """
        画布鼠标释放事件
        """
        pass

    def on_canvas_double_click(self, event):
        """
        画布双击事件（确认裁剪）
        """
        if self.is_cropping and self.crop_rect_id:
            self.perform_crop()

    def on_canvas_right_click(self, event):
        """
        画布右键事件（取消裁剪或魔棒）
        """
        if self.is_cropping:
            self.cancel_crop()
        elif self.is_magic_wanding:
            self.cancel_magic_wand()

    def perform_crop(self):
        """
        执行裁剪
        """
        if not self.crop_rect_id:
            return

        # 获取选区坐标
        coords = self.preview_canvas.coords(self.crop_rect_id)
        if not coords:
            return
            
        x1, y1, x2, y2 = coords
        
        # 规范化坐标
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        # 转换为图像坐标
        offset_x, offset_y = self.preview_offset
        scale = self.preview_scale
        
        img_left = int((left - offset_x) / scale)
        img_top = int((top - offset_y) / scale)
        img_right = int((right - offset_x) / scale)
        img_bottom = int((bottom - offset_y) / scale)
        
        # 边界检查
        img_width, img_height = self.current_screenshot.size
        img_left = max(0, img_left)
        img_top = max(0, img_top)
        img_right = min(img_width, img_right)
        img_bottom = min(img_height, img_bottom)
        
        if img_right <= img_left or img_bottom <= img_top:
            messagebox.showwarning("警告", "裁剪区域无效")
            return

        # 保存撤销状态
        self.push_undo()
        
        # 执行裁剪
        self.current_screenshot = self.current_screenshot.crop((img_left, img_top, img_right, img_bottom))
        
        # 退出裁剪模式
        self.cancel_crop()
        
        # 更新预览
        self.update_preview()
        self.generate_code()

    def cancel_crop(self):
        """
        取消裁剪模式
        """
        self.is_cropping = False
        self.crop_start = None
        if self.crop_rect_id:
            self.preview_canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
        self.preview_canvas.config(cursor="")
    
    def start_magic_wand(self):
        """
        进入魔棒去背景模式
        """
        if not self.current_screenshot:
            return
        
        self.is_magic_wanding = True
        self.preview_canvas.config(cursor="cross")
        messagebox.showinfo("提示", "请在预览区点击要去除的背景色，双击确认，右键取消")
    
    def perform_magic_wand(self, canvas_x, canvas_y):
        """
        执行魔棒去背景
        """
        if not self.current_screenshot:
            return
        
        # 转换画布坐标到图像坐标
        offset_x, offset_y = self.preview_offset
        scale = self.preview_scale
        
        img_x = int((canvas_x - offset_x) / scale)
        img_y = int((canvas_y - offset_y) / scale)
        
        # 边界检查
        img_width, img_height = self.current_screenshot.size
        img_x = max(0, min(img_width - 1, img_x))
        img_y = max(0, min(img_height - 1, img_y))
        
        # 获取点击位置的颜色
        img_array = self.current_screenshot.convert('RGB')
        target_color = img_array.getpixel((img_x, img_y))
        
        # 保存撤销状态
        self.push_undo()
        
        # 转换为 RGBA 以支持透明
        img_rgba = img_array.convert('RGBA')
        pixels = img_rgba.load()
        
        # 遍历所有像素，将相似颜色设为透明
        tolerance = self.magic_wand_tolerance
        for y in range(img_height):
            for x in range(img_width):
                pixel = pixels[x, y]
                r, g, b, a = pixel
                
                # 计算颜色差异
                diff_r = abs(r - target_color[0])
                diff_g = abs(g - target_color[1])
                diff_b = abs(b - target_color[2])
                
                # 如果差异在容差范围内，设为透明
                if diff_r <= tolerance and diff_g <= tolerance and diff_b <= tolerance:
                    pixels[x, y] = (r, g, b, 0)
        
        # 更新当前截图
        self.current_screenshot = img_rgba
        
        # 更新预览
        self.update_preview()
        self.generate_code()
        
        # 退出魔棒模式
        self.cancel_magic_wand()
    
    def cancel_magic_wand(self):
        """
        取消魔棒模式
        """
        self.is_magic_wanding = False
        self.magic_wand_start = None
        if self.magic_wand_rect_id:
            self.preview_canvas.delete(self.magic_wand_rect_id)
            self.magic_wand_rect_id = None
        self.preview_canvas.config(cursor="")
    
    def on_canvas_press(self, event):
        """
        画布鼠标按下事件
        """
        if self.is_cropping:
            self.crop_start = (event.x, event.y)
            if self.crop_rect_id:
                self.preview_canvas.delete(self.crop_rect_id)
                self.crop_rect_id = None
        elif self.is_magic_wanding:
            self.perform_magic_wand(event.x, event.y)

    def _convert_to_grayscale(self, image):
        """
        转换为灰度图
        """
        return image.convert('L')

    def _convert_to_binary(self, image, threshold=127):
        """
        转换为二值化图
        """
        gray = image.convert('L')
        return gray.point(lambda x: 0 if x < threshold else 255, '1')

    def generate_code(self):
        """
        生成 Airtest 代码片段
        """
        if not self.current_screenshot:
            return

        filename = self.filename_var.get() or "screenshot"
        img_width, img_height = self.current_screenshot.size
        
        # 检查图像是否支持透明度（RGBA 模式）
        has_transparency = self.current_screenshot.mode == 'RGBA'
        
        # 生成代码片段（使用虚拟屏分辨率）
        if has_transparency:
            code = f'Template("{filename}.png", record_pos=(0.0, 0.0), resolution=({VIRTUAL_SCREEN_WIDTH}, {VIRTUAL_SCREEN_HEIGHT}), rgb=True)'
        else:
            code = f'Template("{filename}.png", record_pos=(0.0, 0.0), resolution=({VIRTUAL_SCREEN_WIDTH}, {VIRTUAL_SCREEN_HEIGHT}))'

        # 更新代码文本框
        self.code_text.config(state=tk.NORMAL)
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, code)
        self.code_text.config(state=tk.DISABLED)

    def copy_code(self):
        """
        复制代码到剪贴板
        """
        code = self.code_text.get("1.0", tk.END).strip()
        if code and code != "保存截图后将自动生成代码片段...":
            try:
                pyperclip.copy(code)
                messagebox.showinfo("成功", "代码已复制到剪贴板")
            except Exception as e:
                messagebox.showerror("错误", f"复制失败: {e}")
        else:
            messagebox.showwarning("警告", "请先截图")

    def save_screenshot(self):
        """
        保存截图
        """
        if not self.current_screenshot:
            messagebox.showwarning("警告", "请先截图")
            return

        filename = self.filename_var.get()
        if not filename:
            messagebox.showwarning("警告", "请输入文件名")
            return

        # 确保文件名有扩展名
        if not filename.endswith('.png'):
            filename += '.png'

        # 获取保存路径
        save_path = self.save_path_var.get()
        if not save_path:
            messagebox.showwarning("警告", "请选择保存路径")
            return

        # 确保目录存在
        os.makedirs(save_path, exist_ok=True)

        # 保存截图
        filepath = os.path.join(save_path, filename)
        self.current_screenshot.save(filepath)
        self.current_screenshot_path = filepath

        # 保存历史记录
        self.save_history(filename)

        # 保存配置
        self.save_config()

        # 显示成功消息
        messagebox.showinfo("成功", f"截图已保存到:\n{filepath}")

        # 重新生成代码片段（使用实际文件名）
        self.generate_code()

    def on_closing(self):
        """
        关闭窗口时的处理
        """
        # 保存配置
        self.save_config()

        # 关闭区域选择窗口（如果存在）
        if self.region_window:
            self.region_window.destroy()

        self.root.destroy()

    def run(self):
        """
        运行GUI
        """
        self.root.mainloop()


# 测试代码
if __name__ == "__main__":
    tool = ScreenshotTool()
    tool.run()
