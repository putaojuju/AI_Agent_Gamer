# -*- coding: utf-8 -*-
import customtkinter as ctk
import threading
import queue
import time
import os
import json
from PIL import Image, ImageTk
import ctypes

# --- DPI 感知修复 ---
try:
    # Windows 8.1 及以上
    ctypes.windll.shcore.SetProcessDpiAwareness(1) # PROCESS_SYSTEM_DPI_AWARE
except Exception:
    try:
        # Windows Vista/7/8
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass
# -------------------

# 引入项目模块
from game_window import GameWindow
from smart_agent import SmartAgent
from knowledge_manager import KnowledgeBase
from config_manager import ConfigManager
from ai_brain import AIBrain
from logger_setup import logger, write_log

# 设置外观模式
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ============================================================================
# 资源加载器类
# ============================================================================

class AssetManager:
    """
    资源加载器：管理图片资源，当图片不存在时自动生成占位图
    """
    def __init__(self):
        self.assets_dir = "assets"
        if not os.path.exists(self.assets_dir):
            os.makedirs(self.assets_dir)
        
        # 预定义所有需要的图片
        self.required_assets = {
            "bg_curtain": os.path.join(self.assets_dir, "bg_curtain.png"),
            "bg_console": os.path.join(self.assets_dir, "bg_console.png"),
            "avatar_placeholder": os.path.join(self.assets_dir, "avatar_placeholder.png"),
            "projector_off": os.path.join(self.assets_dir, "projector_off.png"),
            "projector_on": os.path.join(self.assets_dir, "projector_on.png"),
            "btn_start": os.path.join(self.assets_dir, "btn_start.png"),
            "btn_stop": os.path.join(self.assets_dir, "btn_stop.png"),
            "btn_config": os.path.join(self.assets_dir, "btn_config.png"),
        }
        
        # 生成所有占位图
        self.generate_placeholders()
    
    def generate_placeholders(self):
        """生成所有占位图片"""
        for name, path in self.required_assets.items():
            if not os.path.exists(path):
                self._create_placeholder(path, name)
    
    def _create_placeholder(self, path, name):
        """创建单个占位图片"""
        # 根据名称生成不同颜色的占位图
        color_map = {
            "bg_curtain": (200, 200, 200),  # 灰色幕布
            "bg_console": (240, 240, 240),  # 白色控制台
            "avatar_placeholder": (180, 210, 240),  # 蓝色看板娘位置
            "projector_off": (120, 120, 120),  # 灰色投影仪（关闭）
            "projector_on": (100, 200, 100),  # 绿色投影仪（开启）
            "btn_start": (50, 200, 50),  # 绿色开始按钮
            "btn_stop": (200, 50, 50),  # 红色停止按钮
            "btn_config": (50, 150, 200),  # 蓝色配置按钮
        }
        
        color = color_map.get(name, (200, 200, 200))
        
        # 根据名称设置不同的尺寸
        size_map = {
            "bg_curtain": (1280, 600),  # 幕布背景
            "bg_console": (1280, 200),  # 控制台背景
            "avatar_placeholder": (200, 200),  # 看板娘
            "projector_off": (80, 80),  # 投影仪
            "projector_on": (80, 80),  # 投影仪
            "btn_start": (60, 60),  # 按钮
            "btn_stop": (60, 60),  # 按钮
            "btn_config": (60, 60),  # 按钮
        }
        
        size = size_map.get(name, (100, 100))
        
        # 创建占位图
        img = Image.new("RGB", size, color)
        img.save(path)
    
    def get_asset(self, name):
        """获取资源路径"""
        return self.required_assets.get(name, None)
    
    def get_image(self, name, size=None):
        """获取图片对象"""
        path = self.get_asset(name)
        if not path or not os.path.exists(path):
            return None
        
        try:
            img = Image.open(path)
            if size:
                img = img.resize(size)
            return img
        except Exception:
            return None
    
    def get_ctk_image(self, name, size=None):
        """获取CTkImage对象"""
        img = self.get_image(name, size)
        if img:
            return ctk.CTkImage(light_image=img, dark_image=img, size=size if size else img.size)
        return None

# ============================================================================
# 核心组件类 - DraggableWindow
# ============================================================================

class DraggableWindow(ctk.CTkFrame):
    """
    可拖拽、可缩放、可堆叠的悬浮窗口组件
    """
    def __init__(self, master, title="Window", width=400, height=300, **kwargs):
        super().__init__(master, width=width, height=height, corner_radius=10, **kwargs)
        
        # 窗口属性
        self.title = title
        self.is_dragging = False
        self.is_resizing = False
        self.start_x = 0
        self.start_y = 0
        self.start_width = width
        self.start_height = height
        self.min_width = 200
        self.min_height = 150
        
        # 设置绝对定位
        self.place(x=100, y=100)
        
        # 创建窗口内容
        self.create_widgets()
        
        # 绑定事件
        self.bind_events()
    
    def create_widgets(self):
        """创建窗口组件"""
        # 1. 标题栏
        self.title_bar = ctk.CTkFrame(self, height=30, fg_color="#34495e", corner_radius=10)
        self.title_bar.pack(fill="x", side="top")
        
        # 标题文本
        self.title_label = ctk.CTkLabel(self.title_bar, text=self.title, font=ctk.CTkFont(size=12, weight="bold"))
        self.title_label.pack(side="left", padx=10, pady=5)
        
        # 关闭按钮
        self.close_btn = ctk.CTkButton(self.title_bar, text="×", width=20, height=20, fg_color="#e74c3c", hover_color="#c0392b", command=self.hide)
        self.close_btn.pack(side="right", padx=5, pady=5)
        
        # 2. 内容容器
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 3. 右下角缩放柄
        self.resize_handle = ctk.CTkFrame(self, width=10, height=10, fg_color="#3498db")
        self.resize_handle.place(x=self.winfo_width()-10, y=self.winfo_height()-10)
    
    def bind_events(self):
        """绑定鼠标事件"""
        # 标题栏拖拽
        self.title_bar.bind("<Button-1>", self.on_drag_start)
        self.title_bar.bind("<B1-Motion>", self.on_drag_motion)
        
        # 窗口点击置顶
        self.bind("<Button-1>", self.on_window_click)
        self.content_frame.bind("<Button-1>", self.on_window_click)
        
        # 缩放柄事件
        self.resize_handle.bind("<Button-1>", self.on_resize_start)
        self.resize_handle.bind("<B1-Motion>", self.on_resize_motion)
        
        # 释放事件
        self.bind("<ButtonRelease-1>", self.on_release)
    
    def on_drag_start(self, event):
        """开始拖拽"""
        self.is_dragging = True
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.lift()  # 点击时置顶
    
    def on_drag_motion(self, event):
        """拖拽中"""
        if not self.is_dragging:
            return
        
        # 计算移动距离
        delta_x = event.x_root - self.start_x
        delta_y = event.y_root - self.start_y
        
        # 获取当前位置
        x = self.winfo_x() + delta_x
        y = self.winfo_y() + delta_y
        
        # 更新位置
        self.place_configure(x=max(0, x), y=max(0, y))
        
        # 更新起始点
        self.start_x = event.x_root
        self.start_y = event.y_root
    
    def on_resize_start(self, event):
        """开始缩放"""
        self.is_resizing = True
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.start_width = self.winfo_width()
        self.start_height = self.winfo_height()
        self.lift()  # 点击时置顶
    
    def on_resize_motion(self, event):
        """缩放中"""
        if not self.is_resizing:
            return
        
        # 计算缩放距离
        delta_x = event.x_root - self.start_x
        delta_y = event.y_root - self.start_y
        
        # 计算新尺寸
        new_width = max(self.min_width, self.start_width + delta_x)
        new_height = max(self.min_height, self.start_height + delta_y)
        
        # 更新尺寸
        self.configure(width=new_width, height=new_height)
        
        # 更新缩放柄位置
        self.resize_handle.place(x=new_width-10, y=new_height-10)
    
    def on_release(self, event):
        """释放鼠标"""
        self.is_dragging = False
        self.is_resizing = False
    
    def on_window_click(self, event):
        """点击窗口时置顶"""
        self.lift()
    
    def show(self):
        """显示窗口"""
        self.lift()
        self.place_configure(state="normal")
    
    def hide(self):
        """隐藏窗口"""
        self.place_forget()
    
    def toggle(self):
        """切换显示/隐藏状态"""
        if self.winfo_ismapped():
            self.hide()
        else:
            self.show()
    
    def get_content_frame(self):
        """获取内容容器"""
        return self.content_frame

# ============================================================================
# 辅助组件类定义 (设置弹窗、日志卡片、日志面板)
# ============================================================================

class SettingsDialog(ctk.CTkToplevel):
    """设置弹窗：用于配置 API Key 和 模型参数"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config = ConfigManager()
        self.title("系统配置 (Settings)")
        self.geometry("500x450")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 225
        self.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.load_current_config()

    def create_widgets(self):
        ctk.CTkLabel(self, text="AI 模型配置", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=30)

        # API Key
        ctk.CTkLabel(self.form_frame, text="API Key:", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_key = ctk.CTkEntry(self.form_frame, placeholder_text="sk-xxxxxxxx", show="*")
        self.entry_key.pack(fill="x", pady=5)
        
        self.show_key = ctk.CTkCheckBox(self.form_frame, text="显示 API Key", command=self.toggle_key_visibility, font=ctk.CTkFont(size=12))
        self.show_key.pack(anchor="w", pady=(0, 10))

        # Endpoint ID
        ctk.CTkLabel(self.form_frame, text="Endpoint ID (火山引擎节点号):", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_endpoint = ctk.CTkEntry(self.form_frame, placeholder_text="ep-2024xxxx-xxxxx")
        self.entry_endpoint.pack(fill="x", pady=5)

        # Model Name
        ctk.CTkLabel(self.form_frame, text="Model Name (模型名称):", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_model = ctk.CTkOptionMenu(self.form_frame, values=["doubao-pro-4k", "doubao-lite-4k", "gpt-4o", "custom"])
        self.entry_model.pack(fill="x", pady=5)

        # 按钮
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20, side="bottom")
        ctk.CTkButton(btn_frame, text="💾 保存配置", fg_color="#27ae60", hover_color="#2ecc71", command=self.save_config).pack(fill="x")

    def toggle_key_visibility(self):
        if self.show_key.get():
            self.entry_key.configure(show="")
        else:
            self.entry_key.configure(show="*")

    def load_current_config(self):
        self.entry_key.insert(0, self.config.get("ai.api_key", ""))
        self.entry_endpoint.insert(0, self.config.get("ai.endpoint_id", ""))
        self.entry_model.set(self.config.get("ai.model", "doubao-pro-4k"))

    def save_config(self):
        self.config.set("ai.api_key", self.entry_key.get().strip())
        self.config.set("ai.endpoint_id", self.entry_endpoint.get().strip())
        self.config.set("ai.model", self.entry_model.get())
        self.parent.add_log("系统配置已更新", type="SYSTEM")
        self.destroy()

class CoTLogCard(ctk.CTkFrame):
    """
    思维链日志卡片 (Chain of Thought Log Card) - V2.0 交互增强版
    特性：全标题点击展开、深色详情背景、紧凑布局
    """
    COLORS = {
        "THOUGHT": "#9b59b6", # 紫色
        "VISION": "#3498db",  # 蓝色
        "ACTION": "#2ecc71",  # 绿色
        "SYSTEM": "#95a5a6",  # 灰色
        "ERROR": "#e74c3c",   # 红色
        "WARNING": "#f39c12"  # 橙色
    }
    ICONS = {
        "THOUGHT": "🧠", "VISION": "👁️", "ACTION": "🖱️", 
        "SYSTEM": "⚙️", "ERROR": "❌", "WARNING": "⚠️"
    }

    def __init__(self, master, log_data: dict, **kwargs):
        # 初始化 Frame，默认背景色即为标题栏颜色
        super().__init__(master, fg_color="#2b2b2b", corner_radius=6, **kwargs)
        
        # --- 1. 数据解析 ---
        raw_type = log_data.get("type", "SYSTEM")
        self.type = raw_type.upper() if raw_type else "SYSTEM"
        self.title = log_data.get("title", log_data.get("text", "Info"))
        self.detail = log_data.get("detail", "")
        
        ts = log_data.get("time", time.time())
        self.timestamp = time.strftime("%H:%M:%S", time.localtime(ts))
        
        self.is_expanded = False
        self.accent_color = self.COLORS.get(self.type, "#95a5a6")
        self.icon = self.ICONS.get(self.type, "📝")

        # --- 2. 标题栏区域 (Header) ---
        # 创建一个内部 Frame 作为标题栏，方便绑定点击事件
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", corner_radius=6)
        self.header_frame.pack(fill="x", ipadx=5, ipady=5) # ipad 增加内部点击区域，但不增加视觉高度
        
        # 左侧彩色指示条
        self.bar = ctk.CTkFrame(self.header_frame, width=4, height=20, fg_color=self.accent_color)
        self.bar.pack(side="left", padx=(5, 5))

        # 时间戳
        self.time_label = ctk.CTkLabel(
            self.header_frame, 
            text=f"[{self.timestamp}]", 
            text_color="#7f8c8d", 
            font=ctk.CTkFont(family="Consolas", size=10)
        )
        self.time_label.pack(side="left", padx=(0, 5))

        # 标题文本
        title_text = f"{self.icon} {self.title}"
        self.info_label = ctk.CTkLabel(
            self.header_frame, 
            text=title_text, 
            font=ctk.CTkFont(size=12, weight="bold"), 
            anchor="w", 
            text_color="#ecf0f1"
        )
        self.info_label.pack(side="left", fill="x", expand=True)

        # 展开/折叠 指示图标
        if self.detail:
            self.arrow_label = ctk.CTkLabel(
                self.header_frame, 
                text="▶", # 初始向右
                width=20, 
                text_color="#7f8c8d", 
                font=ctk.CTkFont(size=10)
            )
            self.arrow_label.pack(side="right", padx=5)

        # --- 3. 详情区域 (Detail) - 初始隐藏 ---
        if self.detail:
            # 详情容器：背景更深
            self.detail_frame = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
            
            # 详情文本框
            self.detail_text = ctk.CTkTextbox(
                self.detail_frame,
                fg_color="transparent", # 透明背景，透出 Frame 的深色
                text_color="#bdc3c7",
                font=ctk.CTkFont(family="Consolas", size=11),
                activate_scrollbars=False,
                height=0 # 初始高度
            )
            self.detail_text.insert("0.0", str(self.detail))
            self.detail_text.configure(state="disabled") # 只读
            self.detail_text.pack(fill="x", padx=10, pady=5)

            # --- 4. 关键：全区域点击绑定 ---
            # 绑定 Header 及其所有子控件，确保点击任何位置都能触发
            self._bind_click_event(self.header_frame)

    def _bind_click_event(self, widget):
        """递归绑定点击事件"""
        widget.bind("<Button-1>", self.toggle_expand)
        for child in widget.winfo_children():
            self._bind_click_event(child)

    def toggle_expand(self, event=None):
        """切换展开/折叠状态"""
        if not self.detail: return
        
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            # 1. 改变箭头方向
            self.arrow_label.configure(text="▼")
            # 2. 改变标题栏背景（可选，增加反馈感）
            self.configure(fg_color="#353535") 
            
            # 3. 显示详情区
            self.detail_frame.pack(fill="x", padx=2, pady=(0, 2))
            
            # 4. 动态计算高度
            line_count = int(self.detail_text.index('end-1c').split('.')[0])
            # 估算高度：行数 * 行高 + 缓冲
            new_height = min(400, max(40, line_count * 18))
            self.detail_text.configure(height=new_height, activate_scrollbars=True)
            
        else:
            # 1. 恢复箭头
            self.arrow_label.configure(text="▶")
            # 2. 恢复标题栏背景
            self.configure(fg_color="#2b2b2b")
            
            # 3. 隐藏详情区
            self.detail_frame.pack_forget()
class ThoughtStreamPanel(ctk.CTkFrame):
    """日志流管理面板"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.log_history = []
        self.current_filter = "ALL"
        
        self.toolbar = ctk.CTkFrame(self, height=40, fg_color="#2b2b2b", corner_radius=0)
        self.toolbar.pack(fill="x", side="top")
        
        ctk.CTkLabel(self.toolbar, text="🧠 思维流", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        self.filter_btn = ctk.CTkSegmentedButton(self.toolbar, values=["ALL", "THOUGHT", "VISION", "ACTION", "SYSTEM"], command=self.apply_filter, width=200, height=24, font=ctk.CTkFont(size=10))
        self.filter_btn.set("ALL")
        self.filter_btn.pack(side="right", padx=10, pady=8)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=2, pady=2)
        self.auto_scroll = True

    def add_log(self, log_data):
        if "time" not in log_data: log_data["time"] = time.time()
        self.log_history.append(log_data)
        if len(self.log_history) > 200: self.log_history.pop(0)
        
        current_type = log_data.get("type", "SYSTEM").upper()
        if self.current_filter == "ALL" or self.current_filter == current_type:
            self._render_card(log_data)

    def _render_card(self, log_data):
        card = CoTLogCard(self.scroll_frame, log_data)
        card.pack(fill="x", pady=2, padx=5)
        if self.auto_scroll:
            self.update_idletasks()
            self.scroll_frame._parent_canvas.yview_moveto(1.0)

    def apply_filter(self, filter_type):
        self.current_filter = filter_type
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        for log in self.log_history:
            log_type = log.get("type", "SYSTEM").upper()
            if filter_type == "ALL" or filter_type == log_type: self._render_card(log)
                
    def clear(self):
        self.log_history.clear()
        for widget in self.scroll_frame.winfo_children(): widget.destroy()

# ============================================================================
# 主程序类 AICmdCenter - 全息投影控制台
# ============================================================================

class AICmdCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Game Agent - 全息投影控制台")
        self.geometry("1280x800")
        self.resizable(True, True)
        
        # 核心模块初始化
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.ui_queue = queue.Queue()
        self.asset_manager = AssetManager()
        
        self.game_window_driver = GameWindow() 
        self.agent = SmartAgent(ui_queue=self.ui_queue, game_window=self.game_window_driver)
        
        # 窗口映射字典
        self.window_map = {}
        
        # 投影仪状态
        self.projector_states = {
            "game": False,
            "log": False
        }

        # 创建分层背景
        self.create_background()
        
        # 创建悬浮窗口
        self.create_floating_windows()
        
        # 创建控制台区域
        self.create_console()
        
        self.running = True
        self.log_thread = threading.Thread(target=self.process_ui_queue, daemon=True)
        self.log_thread.start()
        
        # 初始加载
        self.refresh_game_list()
        self.refresh_window_list() # 自动扫描一次窗口

    def create_background(self):
        """创建分层背景"""
        # Layer 0: 底图（灰色幕布 + 白色控制台）
        self.bg_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.bg_frame.pack(fill="both", expand=True)
        
        # 灰色幕布（投影区）
        self.curtain_frame = ctk.CTkFrame(self.bg_frame, height=600, fg_color="#e0e0e0")
        self.curtain_frame.pack(fill="x", side="top")
        self.curtain_frame.pack_propagate(False)
        
        # 白色控制台桌面
        self.console_frame = ctk.CTkFrame(self.bg_frame, height=200, fg_color="#f5f5f5")
        self.console_frame.pack(fill="x", side="bottom")
        self.console_frame.pack_propagate(False)

    def create_floating_windows(self):
        """创建悬浮窗口"""
        # 游戏画面窗口
        self.win_game = DraggableWindow(self.curtain_frame, title="🎮 游戏画面", width=640, height=480)
        self.win_game.hide()
        
        # 日志窗口
        self.win_log = DraggableWindow(self.curtain_frame, title="🧠 思维流", width=500, height=400)
        self.win_log.hide()
        
        # 填充游戏窗口内容
        self.setup_game_window()
        
        # 填充日志窗口内容
        self.setup_log_window()

    def setup_game_window(self):
        """设置游戏窗口内容"""
        content_frame = self.win_game.get_content_frame()
        
        # 工具栏
        tools = ctk.CTkFrame(content_frame, height=40, fg_color="#2b2b2b")
        tools.pack(fill="x", side="top")
        ctk.CTkLabel(tools, text=" 👁️ 实时视觉 (Live Vision) ", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.view_mode = ctk.CTkSegmentedButton(tools, values=["原始画面", "SoM网格", "UI匹配"], command=self.change_view_mode)
        self.view_mode.set("原始画面")
        self.view_mode.pack(side="right", padx=10, pady=5)

        # 图像容器
        self.image_container = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.image_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_label = ctk.CTkLabel(self.image_container, text="请在控制台选择窗口并连接...", text_color="gray")
        self.preview_label.pack(fill="both", expand=True)

    def setup_log_window(self):
        """设置日志窗口内容"""
        content_frame = self.win_log.get_content_frame()
        
        # 创建思维流面板
        self.thought_panel = ThoughtStreamPanel(content_frame, fg_color="transparent")
        self.thought_panel.pack(fill="both", expand=True)

    def create_console(self):
        """创建控制台区域"""
        # 1. 左侧：看板娘位置
        self.avatar_frame = ctk.CTkFrame(self.console_frame, width=200, height=180, fg_color="#e3f2fd")
        self.avatar_frame.place(x=20, y=10)
        
        avatar_img = self.asset_manager.get_ctk_image("avatar_placeholder", size=(180, 180))
        self.avatar_label = ctk.CTkLabel(self.avatar_frame, image=avatar_img, text="")
        self.avatar_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 2. 中间：游戏配置和窗口选择
        self.control_panel = ctk.CTkFrame(self.console_frame, width=400, height=180, fg_color="transparent")
        self.control_panel.place(x=240, y=10)
        
        # 游戏配置选择
        ctk.CTkLabel(self.control_panel, text="🎮 游戏配置", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        self.game_selector = ctk.CTkOptionMenu(self.control_panel, dynamic_resizing=False, command=self.on_game_change)
        self.game_selector.pack(fill="x", padx=10, pady=(0, 10))
        
        # 窗口连接器
        ctk.CTkLabel(self.control_panel, text="🖥️ 窗口选择", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 容器：放置下拉框和刷新按钮
        win_select_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        win_select_frame.pack(fill="x", padx=10, pady=0)
        
        self.window_selector = ctk.CTkOptionMenu(
            win_select_frame, 
            dynamic_resizing=False,
            values=["请点击刷新..."],
            width=250 
        )
        self.window_selector.pack(side="left", fill="x", expand=True)
        
        self.btn_refresh_win = ctk.CTkButton(
            win_select_frame, text="🔄", width=30, fg_color="#34495e", 
            command=self.refresh_window_list
        )
        self.btn_refresh_win.pack(side="right", padx=(5, 0))
        
        self.btn_link = ctk.CTkButton(
            self.control_panel, text="🔗 锁定选中窗口", fg_color="#2980b9", 
            command=self.link_selected_window
        )
        self.btn_link.pack(fill="x", padx=10, pady=5)
        
        self.lbl_link_status = ctk.CTkLabel(self.control_panel, text="未连接", text_color="gray", font=("Arial", 11))
        self.lbl_link_status.pack(padx=10, pady=2)
        
        # 3. 右侧：投影仪和控制按钮
        self.projector_panel = ctk.CTkFrame(self.console_frame, width=500, height=180, fg_color="transparent")
        self.projector_panel.place(x=660, y=10)
        
        # 投影仪标题
        ctk.CTkLabel(self.projector_panel, text="📽️ 投影仪", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 投影仪按钮容器
        projector_btns_frame = ctk.CTkFrame(self.projector_panel, fg_color="transparent")
        projector_btns_frame.pack(fill="x", padx=10, pady=5)
        
        # 游戏投影仪
        self.btn_projector_game = ctk.CTkButton(
            projector_btns_frame, 
            text="🎮 游戏画面", 
            fg_color="#90caf9", 
            hover_color="#64b5f6",
            width=150,
            command=lambda: self.toggle_projector("game")
        )
        self.btn_projector_game.pack(side="left", padx=10)
        
        # 日志投影仪
        self.btn_projector_log = ctk.CTkButton(
            projector_btns_frame, 
            text="🧠 思维流", 
            fg_color="#90caf9", 
            hover_color="#64b5f6",
            width=150,
            command=lambda: self.toggle_projector("log")
        )
        self.btn_projector_log.pack(side="left", padx=10)
        
        # 控制按钮容器
        control_btns_frame = ctk.CTkFrame(self.projector_panel, fg_color="transparent")
        control_btns_frame.pack(fill="x", padx=10, pady=10)
        
        # 开始按钮
        self.btn_start = ctk.CTkButton(
            control_btns_frame, 
            text="▶ 启动代理", 
            fg_color="#4caf50", 
            hover_color="#45a049",
            width=120,
            state="disabled",
            command=self.start_agent
        )
        self.btn_start.pack(side="left", padx=10)

        # 停止按钮
        self.btn_stop = ctk.CTkButton(
            control_btns_frame, 
            text="⏹ 停止", 
            fg_color="#f44336", 
            hover_color="#da190b",
            width=120,
            state="disabled",
            command=self.stop_agent
        )
        self.btn_stop.pack(side="left", padx=10)

        # 配置按钮
        self.btn_config = ctk.CTkButton(
            control_btns_frame, 
            text="⚙️ 配置", 
            fg_color="#2196f3", 
            hover_color="#0b7dda",
            width=120,
            command=lambda: SettingsDialog(self)
        )
        self.btn_config.pack(side="left", padx=10)

    def toggle_projector(self, projector_type):
        """切换投影仪状态"""
        self.projector_states[projector_type] = not self.projector_states[projector_type]
        
        if projector_type == "game":
            if self.projector_states[projector_type]:
                self.win_game.show()
                self.add_log("游戏投影仪已开启", type="SYSTEM")
            else:
                self.win_game.hide()
                self.add_log("游戏投影仪已关闭", type="SYSTEM")
        elif projector_type == "log":
            if self.projector_states[projector_type]:
                self.win_log.show()
                self.add_log("日志投影仪已开启", type="SYSTEM")
            else:
                self.win_log.hide()
                self.add_log("日志投影仪已关闭", type="SYSTEM")

    # --- 逻辑功能实现 ---

    def refresh_window_list(self):
        """刷新当前打开的窗口列表"""
        windows = self.game_window_driver.get_all_windows()
        self.window_map = {}
        display_list = []
        
        if not windows:
            display_list = ["未发现窗口"]
        else:
            for hwnd, title in windows:
                # 构造唯一名称
                display_name = f"{title} [{hwnd}]"
                if len(display_name) > 30:
                    display_name = display_name[:28] + "..."
                self.window_map[display_name] = hwnd
                display_list.append(display_name)
        
        self.window_selector.configure(values=display_list)
        if display_list: self.window_selector.set(display_list[0])
        
        self.add_log(f"已扫描到 {len(windows)} 个窗口", type="SYSTEM")

    def link_selected_window(self):
        """连接下拉框中选中的窗口"""
        selected_name = self.window_selector.get()
        if selected_name not in self.window_map:
            self.add_log("无效的窗口选择", type="ERROR")
            return
            
        target_hwnd = self.window_map[selected_name]
        
        if self.game_window_driver.init_hwnd(target_hwnd):
            title = self.game_window_driver.window_title
            self.lbl_link_status.configure(text=f"✅ 已连接: {title[:10]}...", text_color="#2ecc71")
            self.btn_start.configure(state="normal")
            self.add_log(f"成功锁定: {title}", type="SYSTEM")
            self.btn_link.configure(fg_color="#27ae60")
            
            # 测试截图
            self.test_snapshot()
        else:
            self.lbl_link_status.configure(text="❌ 连接失败", text_color="#e74c3c")
            self.add_log("无法绑定该窗口句柄", type="ERROR")

    def refresh_game_list(self):
        games = self.knowledge_base.list_games()
        self.game_selector.configure(values=games if games else ["无配置文件"])
        if games: self.game_selector.set(games[0])

    def on_game_change(self, choice):
        self.knowledge_base.load_game(choice)
        self.add_log(f"已加载知识库: {choice}", type="SYSTEM")

    def start_agent(self):
        if not self.game_window_driver.hwnd:
            self.add_log("窗口句柄丢失，请重新连接", type="ERROR")
            return
        self.add_log("正在启动智能代理...", type="SYSTEM")
        
        success = self.agent.start(window_title=None)
        if success:
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.window_selector.configure(state="disabled")
            self.btn_link.configure(state="disabled")
        else:
             self.btn_start.configure(state="normal")

    def stop_agent(self):
        self.agent.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.window_selector.configure(state="normal")
        self.btn_link.configure(state="normal")
        self.add_log("代理已停止", type="SYSTEM")

    def change_view_mode(self, value):
        self.add_log(f"切换视觉模式: {value}", type="SYSTEM")
        # TODO: 传递给 vision_core 处理

    def update_preview(self, img_array):
        try:
            # 将 numpy 数组转换为 PIL Image
            img = Image.fromarray(img_array)
            
            # 获取容器尺寸
            display_w = self.image_container.winfo_width()
            display_h = self.image_container.winfo_height()
            
            # 防止窗口最小化或未渲染时除以零错误
            if display_w < 10 or display_h < 10: 
                return
            
            # 计算缩放比例
            ratio = min(display_w / img.width, display_h / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            
            # 使用 CTkImage
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=new_size
            )
            
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img # 保持引用防止被垃圾回收
            
        except Exception as e: 
            print(f"Preview Error: {e}")

    def process_ui_queue(self):
        while self.running:
            try:
                msg = self.ui_queue.get(timeout=0.1)
                if "image" in msg: 
                    try:
                        self.after(0, self.update_preview, msg["image"])
                    except Exception:
                        pass
                try:
                    self.after(0, lambda: self.thought_panel.add_log(msg))
                    # 同时写入日志文件
                    write_log(msg)
                except Exception:
                    pass
                self.ui_queue.task_done()
            except queue.Empty: 
                continue
            except Exception:
                # 捕获UI已销毁的异常
                break
            
    def add_log(self, text, detail="", type="SYSTEM"):
        # 将 key 从 "text" 改为 "title"，与 SmartAgent 保持一致
        self.ui_queue.put({"title": text, "detail": detail, "type": type})
    
    def test_snapshot(self):
        img = self.game_window_driver.snapshot()
        if img is not None:
            self.update_preview(img)
            self.add_log("视觉信号接入正常", type="VISION")
        else:
            self.add_log("窗口连接成功，但画面黑屏或受保护", type="ERROR")

    def on_closing(self):
        self.running = False
        self.stop_agent()
        # 关闭日志文件
        logger.close()
        self.destroy()

if __name__ == "__main__":
    app = AICmdCenter()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()