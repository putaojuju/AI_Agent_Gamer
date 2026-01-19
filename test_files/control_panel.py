# -*- coding: utf-8 -*-
"""
控制面板GUI
用于管理虚拟屏幕和独立鼠标，显示系统状态和日志
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import logging
from mss import mss
from PIL import Image, ImageTk
import numpy as np
import cv2
import win32gui
import win32con
from virtual_display import virtual_display_manager
from independent_mouse import independent_mouse
from game_window_manager import game_window_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('control_panel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('control_panel')

class ControlPanel:
    """
    控制面板GUI
    """
    
    def __init__(self):
        """
        初始化控制面板
        """
        self.root = tk.Tk()
        self.root.title("虚拟屏幕独立鼠标控制面板")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置主题
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 日志文本框
        self.log_text = None
        
        # 显示器信息列表
        self.display_tree = None
        
        # 游戏窗口列表
        self.window_tree = None
        
        # 创建UI
        self.create_widgets()
        
        # 启动定时更新线程
        self.running = True
        self.update_thread = threading.Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """
        创建GUI组件
        """
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建笔记本组件
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 状态监控标签页
        status_frame = ttk.Frame(notebook, padding="10")
        notebook.add(status_frame, text="状态监控")
        
        # 显示器信息标签页
        display_frame = ttk.Frame(notebook, padding="10")
        notebook.add(display_frame, text="显示器信息")
        
        # 游戏窗口管理标签页
        window_frame = ttk.Frame(notebook, padding="10")
        notebook.add(window_frame, text="游戏窗口管理")
        
        # 虚拟屏幕预览标签页
        virtual_preview_frame = ttk.Frame(notebook, padding="10")
        notebook.add(virtual_preview_frame, text="虚拟屏幕预览")
        
        # 日志标签页
        log_frame = ttk.Frame(notebook, padding="10")
        notebook.add(log_frame, text="日志")
        
        # 创建状态监控页面
        self.create_status_page(status_frame)
        
        # 创建显示器信息页面
        self.create_display_page(display_frame)
        
        # 创建游戏窗口管理页面
        self.create_window_page(window_frame)
        
        # 创建虚拟屏幕预览页面
        self.create_virtual_preview_page(virtual_preview_frame)
        
        # 创建日志页面
        self.create_log_page(log_frame)
    
    def create_status_page(self, parent):
        """
        创建状态监控页面
        """
        # 创建状态框架
        status_grid = ttk.Frame(parent)
        status_grid.pack(fill=tk.BOTH, expand=True)
        
        # 系统状态
        ttk.Label(status_grid, text="系统状态", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # 主屏幕信息
        ttk.Label(status_grid, text="主屏幕:", anchor=tk.W).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.main_display_var = tk.StringVar()
        ttk.Label(status_grid, textvariable=self.main_display_var, anchor=tk.W).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 虚拟屏幕信息
        ttk.Label(status_grid, text="虚拟屏幕:", anchor=tk.W).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.virtual_display_var = tk.StringVar()
        ttk.Label(status_grid, textvariable=self.virtual_display_var, anchor=tk.W).grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 独立鼠标状态
        ttk.Label(status_grid, text="独立鼠标状态:", anchor=tk.W).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.mouse_status_var = tk.StringVar()
        ttk.Label(status_grid, textvariable=self.mouse_status_var, anchor=tk.W).grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 目标显示器
        ttk.Label(status_grid, text="目标显示器:", anchor=tk.W).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_display_var = tk.StringVar()
        ttk.Label(status_grid, textvariable=self.target_display_var, anchor=tk.W).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 更新按钮
        ttk.Button(status_grid, text="刷新状态", command=self.update_status).grid(row=5, column=0, columnspan=2, pady=10)
    
    def create_display_page(self, parent):
        """
        创建显示器信息页面
        """
        # 创建显示器信息表格
        ttk.Label(parent, text="显示器信息", font=("Arial", 14, "bold")).pack(pady=10)
        
        # 创建树视图
        columns = ("id", "name", "position", "size", "refresh_rate", "bit_depth", "is_primary")
        self.display_tree = ttk.Treeview(parent, columns=columns, show="headings")
        
        # 设置列标题
        self.display_tree.heading("id", text="ID")
        self.display_tree.heading("name", text="名称")
        self.display_tree.heading("position", text="位置")
        self.display_tree.heading("size", text="分辨率")
        self.display_tree.heading("refresh_rate", text="刷新率")
        self.display_tree.heading("bit_depth", text="颜色深度")
        self.display_tree.heading("is_primary", text="主屏幕")
        
        # 设置列宽
        self.display_tree.column("id", width=50, anchor=tk.CENTER)
        self.display_tree.column("name", width=150, anchor=tk.W)
        self.display_tree.column("position", width=100, anchor=tk.CENTER)
        self.display_tree.column("size", width=100, anchor=tk.CENTER)
        self.display_tree.column("refresh_rate", width=100, anchor=tk.CENTER)
        self.display_tree.column("bit_depth", width=100, anchor=tk.CENTER)
        self.display_tree.column("is_primary", width=80, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.display_tree.yview)
        self.display_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.display_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 刷新按钮
        ttk.Button(parent, text="刷新显示器信息", command=self.update_display_info).pack(pady=10)
    
    def create_window_page(self, parent):
        """
        创建游戏窗口管理页面
        """
        # 创建游戏窗口管理框架
        window_grid = ttk.Frame(parent)
        window_grid.pack(fill=tk.BOTH, expand=True)
        
        # 窗口列表
        ttk.Label(window_grid, text="游戏窗口列表", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # 创建窗口树视图
        columns = ("hwnd", "title", "class_name", "size", "position", "on_virtual")
        self.window_tree = ttk.Treeview(window_grid, columns=columns, show="headings")
        
        # 设置列标题
        self.window_tree.heading("hwnd", text="句柄")
        self.window_tree.heading("title", text="标题")
        self.window_tree.heading("class_name", text="类名")
        self.window_tree.heading("size", text="大小")
        self.window_tree.heading("position", text="位置")
        self.window_tree.heading("on_virtual", text="在虚拟屏幕上")
        
        # 设置列宽
        self.window_tree.column("hwnd", width=100, anchor=tk.CENTER)
        self.window_tree.column("title", width=200, anchor=tk.W)
        self.window_tree.column("class_name", width=120, anchor=tk.W)
        self.window_tree.column("size", width=100, anchor=tk.CENTER)
        self.window_tree.column("position", width=100, anchor=tk.CENTER)
        self.window_tree.column("on_virtual", width=120, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(window_grid, orient=tk.VERTICAL, command=self.window_tree.yview)
        self.window_tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.window_tree.grid(row=1, column=0, rowspan=4, sticky=tk.NSEW, padx=5)
        scrollbar.grid(row=1, column=1, rowspan=4, sticky=tk.NS, padx=5)
        
        # 操作按钮
        ttk.Button(window_grid, text="刷新窗口列表", command=self.update_window_list).grid(row=1, column=2, pady=5, padx=5, sticky=tk.EW)
        ttk.Button(window_grid, text="移动到虚拟屏幕", command=self.move_selected_window_to_virtual).grid(row=2, column=2, pady=5, padx=5, sticky=tk.EW)
        ttk.Button(window_grid, text="移动到主屏幕", command=self.move_selected_window_to_main).grid(row=3, column=2, pady=5, padx=5, sticky=tk.EW)
        ttk.Button(window_grid, text="最大化窗口", command=self.maximize_selected_window).grid(row=4, column=2, pady=5, padx=5, sticky=tk.EW)
        
        # 窗口搜索
        ttk.Label(window_grid, text="搜索窗口标题:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(window_grid, textvariable=self.search_var)
        search_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Button(window_grid, text="搜索", command=self.search_windows).grid(row=5, column=2, padx=5, pady=5, sticky=tk.EW)
        
        # 设置网格权重
        window_grid.columnconfigure(0, weight=1)
        window_grid.rowconfigure(1, weight=1)
    
    def create_virtual_preview_page(self, parent):
        """
        创建虚拟屏幕预览页面
        """
        # 创建预览框架
        preview_grid = ttk.Frame(parent)
        preview_grid.pack(fill=tk.BOTH, expand=True)
        
        # 预览标题
        ttk.Label(preview_grid, text="虚拟屏幕实时预览", font=(("Arial", 14, "bold"))).pack(pady=10)
        
        # 预览画布框架
        canvas_frame = ttk.Frame(preview_grid, relief=tk.SUNKEN, borderwidth=1)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建画布
        self.preview_canvas = tk.Canvas(canvas_frame, bg="#000000")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 预览控制框架
        control_frame = ttk.Frame(preview_grid)
        control_frame.pack(fill=tk.X, pady=5)
        
        # 预览状态
        self.preview_status_var = tk.StringVar(value="未开始预览")
        ttk.Label(control_frame, textvariable=self.preview_status_var).pack(side=tk.LEFT, padx=5)
        
        # 刷新频率选择
        ttk.Label(control_frame, text="刷新频率:").pack(side=tk.LEFT, padx=5)
        self.refresh_rate_var = tk.StringVar(value="1")
        refresh_rate_combo = ttk.Combobox(
            control_frame,
            textvariable=self.refresh_rate_var,
            values=["0.5", "1", "2", "5"],
            state="readonly"
        )
        refresh_rate_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(control_frame, text="秒").pack(side=tk.LEFT)
        
        # 手动刷新按钮
        ttk.Button(control_frame, text="手动刷新", command=self.refresh_virtual_preview).pack(side=tk.RIGHT, padx=5)
        
        # 开始/停止预览按钮
        self.preview_running = False
        self.preview_button = ttk.Button(control_frame, text="开始预览", command=self.toggle_preview)
        self.preview_button.pack(side=tk.RIGHT, padx=5)
        
        # 初始化预览图像
        self.preview_image = None
        
        # 显示提示信息
        self.preview_canvas.create_text(
            200, 150,
            text="点击'开始预览'查看虚拟屏幕内容",
            fill="#ffffff",
            font=(("Arial", 12))
        )
    
    def toggle_preview(self):
        """
        切换预览状态
        """
        if self.preview_running:
            # 停止预览
            self.preview_running = False
            self.preview_button.config(text="开始预览")
            self.preview_status_var.set("预览已停止")
        else:
            # 开始预览
            self.preview_running = True
            self.preview_button.config(text="停止预览")
            self.preview_status_var.set("预览中...")
            # 启动预览更新线程
            threading.Thread(target=self.preview_loop, daemon=True).start()
    
    def preview_loop(self):
        """
        预览更新循环
        """
        import time
        frame_count = 0
        start_time = time.time()
        
        while self.preview_running:
            # 记录开始时间
            frame_start = time.time()
            
            # 更新预览
            self.root.after(0, self.refresh_virtual_preview)
            
            # 计算并记录帧时间
            frame_time = time.time() - frame_start
            frame_count += 1
            
            # 每10帧计算一次帧率
            if frame_count % 10 == 0:
                elapsed_time = time.time() - start_time
                fps = frame_count / elapsed_time
                logger.debug(f"Preview FPS: {fps:.2f}, Frame time: {frame_time*1000:.2f}ms")
            
            # 获取刷新频率
            refresh_rate = float(self.refresh_rate_var.get())
            time.sleep(refresh_rate)
    
    def refresh_virtual_preview(self):
        """
        刷新虚拟屏幕预览
        """
        try:
            # 获取虚拟屏幕信息
            virtual_display_manager.update_displays_info()
            virtual_display = virtual_display_manager.get_virtual_display()
            
            if not virtual_display:
                self.preview_status_var.set("未检测到虚拟屏幕")
                return
            
            # 获取虚拟屏幕的位置和大小
            left = virtual_display['left']
            top = virtual_display['top']
            width = virtual_display['width']
            height = virtual_display['height']
            
            # 截图虚拟屏幕区域（使用mss库提高性能）
            self.preview_status_var.set("正在截图...")
            
            # 使用mss进行快速截图
            with mss() as sct:
                # 创建截图区域
                monitor = {
                    "left": left,
                    "top": top,
                    "width": width,
                    "height": height
                }
                # 直接从内存获取像素数据
                screenshot = sct.grab(monitor)
                # 转换为numpy数组（OpenCV格式）
                img_np = np.array(screenshot)[:, :, :3]  # 去除alpha通道
            
            # 调整截图大小以适应画布
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width > 0 and canvas_height > 0:
                # 计算缩放比例
                scale = min(canvas_width / width, canvas_height / height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # 使用OpenCV进行高效图像缩放
                # INTER_LINEAR：双线性插值，速度快，质量好
                # INTER_AREA：区域插值，适合缩小图像
                interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
                img_resized = cv2.resize(img_np, (new_width, new_height), interpolation=interpolation)
                
                # 将OpenCV图像转换为PIL图像
                # OpenCV使用BGR格式，需要转换为RGB格式
                img_resized = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
                resized_screenshot = Image.fromarray(img_resized)
                
                # 转换为Tkinter图像
                self.preview_image = ImageTk.PhotoImage(resized_screenshot)
                
                # 清除画布
                self.preview_canvas.delete("all")
                
                # 计算居中位置
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                
                # 显示图像
                self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.preview_image)
                
                self.preview_status_var.set(f"预览中 - 分辨率: {width}x{height}")
        except Exception as e:
            logger.error(f"刷新虚拟屏幕预览失败: {e}")
            self.preview_status_var.set(f"预览错误: {str(e)}")
    
    def create_log_page(self, parent):
        """
        创建日志页面
        """
        # 创建日志框架
        log_grid = ttk.Frame(parent)
        log_grid.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志文本框
        self.log_text = scrolledtext.ScrolledText(
            log_grid,
            wrap=tk.WORD,
            width=80,
            height=20,
            font=("Courier New", 10)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志级别选择
        level_frame = ttk.Frame(log_grid)
        level_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_frame, text="日志级别:").pack(side=tk.LEFT, padx=5)
        level_var = tk.StringVar(value="INFO")
        level_combo = ttk.Combobox(
            level_frame,
            textvariable=level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly"
        )
        level_combo.pack(side=tk.LEFT, padx=5)
        
        # 清空日志按钮
        ttk.Button(level_frame, text="清空日志", command=self.clear_log).pack(side=tk.RIGHT, padx=5)
        
        # 刷新日志按钮
        ttk.Button(level_frame, text="刷新日志", command=self.refresh_log).pack(side=tk.RIGHT, padx=5)
    
    def update_status(self):
        """
        更新系统状态
        """
        # 更新显示器信息
        virtual_display_manager.update_displays_info()
        
        # 更新主屏幕信息
        main_display = virtual_display_manager.get_main_display()
        if main_display:
            main_info = f"{main_display['width']}x{main_display['height']}, {main_display['refresh_rate']}Hz"
            self.main_display_var.set(main_info)
        else:
            self.main_display_var.set("未检测到主屏幕")
        
        # 更新虚拟屏幕信息
        virtual_display = virtual_display_manager.get_virtual_display()
        if virtual_display:
            virtual_info = f"{virtual_display['width']}x{virtual_display['height']}, {virtual_display['refresh_rate']}Hz"
            self.virtual_display_var.set(virtual_info)
        else:
            self.virtual_display_var.set("未检测到虚拟屏幕")
        
        # 更新独立鼠标状态
        mouse_status = "已启用" if independent_mouse else "已禁用"
        self.mouse_status_var.set(mouse_status)
        
        # 更新目标显示器
        target_display = independent_mouse.target_display
        if target_display:
            target_info = f"显示器 {target_display['id']}: {target_display['width']}x{target_display['height']}"
            self.target_display_var.set(target_info)
        else:
            self.target_display_var.set("未设置")
    
    def update_display_info(self):
        """
        更新显示器信息
        """
        # 清空现有数据
        for item in self.display_tree.get_children():
            self.display_tree.delete(item)
        
        # 更新显示器信息
        virtual_display_manager.update_displays_info()
        displays = virtual_display_manager.get_displays()
        
        # 添加显示器信息到表格
        for display in displays:
            self.display_tree.insert("", tk.END, values=(
                display['id'],
                display['name'],
                f"({display['left']}, {display['top']})",
                f"{display['width']}x{display['height']}",
                f"{display['refresh_rate']}Hz",
                f"{display['bit_depth']}位",
                "是" if display['is_primary'] else "否"
            ))
    
    def update_window_list(self):
        """
        更新游戏窗口列表
        """
        # 清空现有数据
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)
        
        # 更新游戏窗口信息
        game_window_manager.update_game_windows()
        for hwnd, window_info in game_window_manager.game_windows.items():
            # 检查窗口是否在虚拟屏幕上
            is_on_virtual = game_window_manager.is_window_on_virtual_screen(hwnd)
            
            self.window_tree.insert("", tk.END, values=(
                hwnd,
                window_info['title'],
                window_info['class_name'],
                f"{window_info['width']}x{window_info['height']}",
                f"({window_info['left']}, {window_info['top']})",
                "是" if is_on_virtual else "否"
            ), tags=("virtual" if is_on_virtual else "main"))
        
        # 设置标签样式
        self.window_tree.tag_configure("virtual", background="#e0f7fa")
        self.window_tree.tag_configure("main", background="#f3e5f5")
    
    def move_selected_window_to_virtual(self):
        """
        将选中的窗口移动到虚拟屏幕
        """
        selected_items = self.window_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个窗口")
            return
        
        for item in selected_items:
            hwnd = int(self.window_tree.item(item, "values")[0])
            success = game_window_manager.move_game_to_virtual_screen(hwnd)
            if success:
                messagebox.showinfo("成功", f"窗口 {hwnd} 已移动到虚拟屏幕")
            else:
                messagebox.showerror("失败", f"移动窗口 {hwnd} 到虚拟屏幕失败")
        
        # 更新窗口列表
        self.update_window_list()
    
    def move_selected_window_to_main(self):
        """
        将选中的窗口移动到主屏幕
        """
        selected_items = self.window_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个窗口")
            return
        
        for item in selected_items:
            hwnd = int(self.window_tree.item(item, "values")[0])
            success = game_window_manager.move_game_to_main_screen(hwnd)
            if success:
                messagebox.showinfo("成功", f"窗口 {hwnd} 已移动到主屏幕")
            else:
                messagebox.showerror("失败", f"移动窗口 {hwnd} 到主屏幕失败")
        
        # 更新窗口列表
        self.update_window_list()
    
    def maximize_selected_window(self):
        """
        最大化选中的窗口
        """
        selected_items = self.window_tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请选择一个窗口")
            return
        
        for item in selected_items:
            hwnd = int(self.window_tree.item(item, "values")[0])
            success = game_window_manager.maximize_window(hwnd)
            if success:
                messagebox.showinfo("成功", f"窗口 {hwnd} 已最大化")
            else:
                messagebox.showerror("失败", f"最大化窗口 {hwnd} 失败")
        
        # 更新窗口列表
        self.update_window_list()
    
    def search_windows(self):
        """
        搜索窗口
        """
        search_text = self.search_var.get()
        if not search_text:
            self.update_window_list()
            return
        
        # 清空现有数据
        for item in self.window_tree.get_children():
            self.window_tree.delete(item)
        
        # 搜索窗口
        game_window_manager.update_game_windows()
        for hwnd, window_info in game_window_manager.game_windows.items():
            if search_text.lower() in window_info['title'].lower():
                # 检查窗口是否在虚拟屏幕上
                is_on_virtual = game_window_manager.is_window_on_virtual_screen(hwnd)
                
                self.window_tree.insert("", tk.END, values=(
                    hwnd,
                    window_info['title'],
                    window_info['class_name'],
                    f"{window_info['width']}x{window_info['height']}",
                    f"({window_info['left']}, {window_info['top']})",
                    "是" if is_on_virtual else "否"
                ), tags=("virtual" if is_on_virtual else "main"))
    
    def clear_log(self):
        """
        清空日志
        """
        self.log_text.delete("1.0", tk.END)
    
    def refresh_log(self):
        """
        刷新日志
        """
        self.clear_log()
        try:
            with open("control_panel.log", "r", encoding="utf-8") as f:
                log_content = f.read()
                self.log_text.insert(tk.END, log_content)
        except Exception as e:
            messagebox.showerror("错误", f"读取日志文件失败: {e}")
    
    def update_loop(self):
        """
        定时更新线程
        """
        while self.running:
            # 更新状态
            self.root.after(0, self.update_status)
            
            # 每5秒更新一次显示器和窗口信息
            self.root.after(0, self.update_display_info)
            self.root.after(0, self.update_window_list)
            
            # 每10秒刷新一次日志
            self.root.after(0, self.refresh_log)
            
            # 休眠5秒
            time.sleep(5)
    
    def on_closing(self):
        """
        关闭窗口时的处理
        """
        self.running = False
        self.root.destroy()
    
    def run(self):
        """
        运行GUI
        """
        self.root.mainloop()

# 测试代码
if __name__ == "__main__":
    panel = ControlPanel()
    panel.run()
