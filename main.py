# -*- coding: utf-8 -*-
import customtkinter as ctk
import threading
import queue
import time
import os
import json
from PIL import Image, ImageTk

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
# 主程序类 AICmdCenter
# ============================================================================

class AICmdCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Game Agent - Command Center")
        self.geometry("1280x800")
        
        # 核心模块初始化
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.ui_queue = queue.Queue()
        
        self.game_window_driver = GameWindow() 
        self.agent = SmartAgent(ui_queue=self.ui_queue, game_window=self.game_window_driver)
        
        # 窗口映射字典
        self.window_map = {}

        # 布局配置
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_viewport()
        self.create_thought_stream()
        
        self.running = True
        self.log_thread = threading.Thread(target=self.process_ui_queue, daemon=True)
        self.log_thread.start()
        
        # 初始加载
        self.refresh_game_list()
        self.refresh_window_list() # 自动扫描一次窗口

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # 1. 标题
        ctk.CTkLabel(self.sidebar, text="🤖 AI AGENT", font=("Arial", 20, "bold")).pack(pady=(20, 5))
        
        # 2. 游戏配置选择
        ctk.CTkLabel(self.sidebar, text="1. 游戏配置 (Game Config)", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=15, pady=(15, 5))
        self.game_selector = ctk.CTkOptionMenu(self.sidebar, dynamic_resizing=False, command=self.on_game_change)
        self.game_selector.pack(fill="x", padx=15)

        # 3. 窗口连接器 (下拉列表)
        ctk.CTkLabel(self.sidebar, text="2. 锁定窗口 (Select Window)", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=15, pady=(20, 5))
        
        # 容器：放置下拉框和刷新按钮
        win_select_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        win_select_frame.pack(fill="x", padx=15, pady=5)
        
        self.window_selector = ctk.CTkOptionMenu(
            win_select_frame, 
            dynamic_resizing=False,
            values=["请点击刷新..."],
            width=160 
        )
        self.window_selector.pack(side="left", fill="x", expand=True)
        
        self.btn_refresh_win = ctk.CTkButton(
            win_select_frame, text="🔄", width=30, fg_color="#34495e", 
            command=self.refresh_window_list
        )
        self.btn_refresh_win.pack(side="right", padx=(5, 0))
        
        self.btn_link = ctk.CTkButton(
            self.sidebar, text="🔗 锁定选中窗口", fg_color="#2980b9", 
            command=self.link_selected_window
        )
        self.btn_link.pack(fill="x", padx=15, pady=5)
        
        self.lbl_link_status = ctk.CTkLabel(self.sidebar, text="未连接", text_color="gray", font=("Arial", 11))
        self.lbl_link_status.pack(pady=2)

        # 4. 运行控制
        ctk.CTkLabel(self.sidebar, text="3. 运行控制 (Control)", anchor="w", font=("Arial", 12, "bold")).pack(fill="x", padx=15, pady=(30, 5))
        
        self.btn_start = ctk.CTkButton(
            self.sidebar, text="▶ 启动代理", fg_color="#27ae60", hover_color="#2ecc71",
            height=40, font=("Arial", 14, "bold"), state="disabled",
            command=self.start_agent
        )
        self.btn_start.pack(fill="x", padx=15, pady=5)

        self.btn_stop = ctk.CTkButton(
            self.sidebar, text="⏹ 停止", fg_color="#c0392b", hover_color="#e74c3c",
            height=40, font=("Arial", 14, "bold"), state="disabled",
            command=self.stop_agent
        )
        self.btn_stop.pack(fill="x", padx=15, pady=5)

        # 5. 底部设置
        ctk.CTkButton(self.sidebar, text="⚙️ 系统配置", fg_color="#34495e", command=lambda: SettingsDialog(self)).pack(side="bottom", fill="x", padx=15, pady=20)

    def create_viewport(self):
        self.viewport = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.viewport.grid(row=0, column=1, sticky="nsew", padx=2)
        
        tools = ctk.CTkFrame(self.viewport, height=40, fg_color="#2b2b2b")
        tools.pack(fill="x", side="top")
        ctk.CTkLabel(tools, text=" 👁️ 实时视觉 (Live Vision) ", font=("Arial", 12, "bold")).pack(side="left", padx=10)
        self.view_mode = ctk.CTkSegmentedButton(tools, values=["原始画面", "SoM网格", "UI匹配"], command=self.change_view_mode)
        self.view_mode.set("原始画面")
        self.view_mode.pack(side="right", padx=10, pady=5)

        self.image_container = ctk.CTkFrame(self.viewport, fg_color="transparent")
        self.image_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_label = ctk.CTkLabel(self.image_container, text="请在左侧选择窗口并连接...", text_color="gray")
        self.preview_label.pack(fill="both", expand=True)

    def create_thought_stream(self):
        self.thought_panel = ThoughtStreamPanel(self, width=380, corner_radius=0)
        self.thought_panel.grid(row=0, column=2, sticky="nsew")
        self.thought_panel.grid_propagate(False)

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
        if display_list:
            self.window_selector.set(display_list[0])
        
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
            
            # --- FIX START: 使用 CTkImage 替代 ImageTk.PhotoImage ---
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=new_size
            )
            # --- FIX END ---
            
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