# -*- coding: utf-8 -*-
import customtkinter as ctk
import threading
import queue
import time
import os
from PIL import Image, ImageTk
import logging

# 引入项目模块
from game_window import GameWindow
from smart_agent import SmartAgent
from knowledge_manager import KnowledgeBase
from config_manager import ConfigManager

# 设置外观模式
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class ModernLogCard(ctk.CTkFrame):
    """
    现代化的日志卡片，带有状态色条和折叠功能
    """
    COLORS = {
        "thought": "#8e44ad",  # 紫色：AI思考
        "vision":  "#2980b9",  # 蓝色：视觉感知
        "action":  "#27ae60",  # 绿色：执行操作
        "error":   "#c0392b",  # 红色：错误
        "system":  "#7f8c8d"   # 灰色：系统消息
    }
    
    ICONS = {
        "thought": "🧠",
        "vision":  "👁️",
        "action":  "🖱️",
        "error":   "❌",
        "system":  "⚙️"
    }

    def __init__(self, master, text, detail="", type="system", timestamp=None, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", corner_radius=6, **kwargs)
        
        self.detail = detail
        self.is_expanded = False
        accent_color = self.COLORS.get(type, self.COLORS["system"])
        icon = self.ICONS.get(type, "📝")
        time_str = timestamp if timestamp else time.strftime("%H:%M:%S")

        # 1. 左侧彩色状态条
        self.bar = ctk.CTkFrame(self, width=4, fg_color=accent_color, corner_radius=0)
        self.bar.pack(side="left", fill="y", padx=(0, 5))

        # 2. 内容容器
        self.content_box = ctk.CTkFrame(self, fg_color="transparent")
        self.content_box.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # 3. 标题行 (图标 + 时间 + 摘要)
        self.header_frame = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.header_frame.pack(fill="x")

        self.info_label = ctk.CTkLabel(
            self.header_frame, 
            text=f"{icon} [{time_str}] {text}",
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w",
            text_color="#ecf0f1"
        )
        self.info_label.pack(side="left", fill="x", expand=True)

        # 4. 展开/折叠按钮 (如果有详细信息)
        if detail:
            self.expand_btn = ctk.CTkButton(
                self.header_frame, text="▼", width=20, height=20,
                fg_color="transparent", text_color="#95a5a6",
                command=self.toggle_expand
            )
            self.expand_btn.pack(side="right")
            
            # 详细信息区域 (默认隐藏)
            self.detail_label = ctk.CTkTextbox(
                self.content_box, height=0, fg_color="#1e1e1e", 
                text_color="#bdc3c7", font=ctk.CTkFont(family="Consolas", size=11)
            )
            self.detail_label.insert("0.0", detail)
            self.detail_label.configure(state="disabled")

            # 绑定点击事件到整个头部
            self.info_label.bind("<Button-1>", lambda e: self.toggle_expand())

    def toggle_expand(self):
        if not self.detail: return
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.expand_btn.configure(text="▲")
            self.detail_label.pack(fill="x", pady=(5, 0))
            self.detail_label.configure(height=100) # 展开高度
        else:
            self.expand_btn.configure(text="▼")
            self.detail_label.pack_forget()

class AICmdCenter(ctk.CTk):
    """
    AI 游戏代理指挥中心 - 主窗口
    """
    def __init__(self):
        super().__init__()
        
        # 1. 基础窗口设置
        self.title("AI Game Agent - Command Center")
        self.geometry("1280x800")
        self.minsize(1000, 700)
        
        # 初始化核心模块
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.ui_queue = queue.Queue()
        self.agent = SmartAgent(ui_queue=self.ui_queue)
        
        # 布局配置 (三栏布局: Sidebar, Viewport, ThoughtStream)
        self.grid_columnconfigure(1, weight=3) # 中间视窗权重最大
        self.grid_columnconfigure(2, weight=1) # 右侧日志权重适中
        self.grid_rowconfigure(0, weight=1)

        # 构建三大区域
        self.create_sidebar()
        self.create_viewport()
        self.create_thought_stream()
        
        # 启动UI更新循环
        self.running = True
        self.log_thread = threading.Thread(target=self.process_ui_queue, daemon=True)
        self.log_thread.start()
        
        # 初始加载
        self.refresh_game_list()

    def create_sidebar(self):
        """左侧控制栏：状态与控制"""
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False) # 固定宽度

        # Logo / 标题
        ctk.CTkLabel(self.sidebar, text="🤖 AI AGENT", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self.sidebar, text="v1.0.0", text_color="gray").pack(pady=(0, 20))

        # 游戏选择
        ctk.CTkLabel(self.sidebar, text="目标游戏 (Target Game)", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.game_selector = ctk.CTkOptionMenu(self.sidebar, dynamic_resizing=False, command=self.on_game_change)
        self.game_selector.pack(fill="x", padx=20, pady=5)

        # 状态指示
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=20)
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="red", font=("Arial", 24))
        self.status_dot.pack(side="left")
        self.status_text = ctk.CTkLabel(self.status_frame, text=" 已停止 (Stopped)", anchor="w")
        self.status_text.pack(side="left", padx=10)

        # 核心控制按钮 (大按钮)
        self.btn_start = ctk.CTkButton(
            self.sidebar, text="▶ 启动代理 (START)", 
            fg_color="#27ae60", hover_color="#2ecc71",
            height=40, font=ctk.CTkFont(weight="bold"),
            command=self.start_agent
        )
        self.btn_start.pack(fill="x", padx=20, pady=(10, 5))

        self.btn_stop = ctk.CTkButton(
            self.sidebar, text="⏹ 停止代理 (STOP)", 
            fg_color="#c0392b", hover_color="#e74c3c",
            height=40, font=ctk.CTkFont(weight="bold"),
            state="disabled",
            command=self.stop_agent
        )
        self.btn_stop.pack(fill="x", padx=20, pady=5)

        # 调试工具
        ctk.CTkLabel(self.sidebar, text="调试工具", anchor="w").pack(fill="x", padx=20, pady=(30, 0))
        self.debug_switch = ctk.CTkSwitch(self.sidebar, text="调试模式 (Debug Mode)", command=self.toggle_debug)
        self.debug_switch.pack(fill="x", padx=20, pady=10)
        
        if self.config_manager.get("debug.enabled"):
            self.debug_switch.select()

        # 底部占位
        ctk.CTkLabel(self.sidebar, text="System Ready", font=("Consolas", 10), text_color="gray").pack(side="bottom", pady=20)

    def create_viewport(self):
        """中间视窗：视觉感知区域"""
        self.viewport = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.viewport.grid(row=0, column=1, sticky="nsew", padx=2)
        
        # 顶部工具栏
        self.view_tools = ctk.CTkFrame(self.viewport, height=40, fg_color="#2b2b2b")
        self.view_tools.pack(fill="x", side="top")
        
        ctk.CTkLabel(self.view_tools, text=" 👁️ 视觉感知 (Visual Perception) ", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        
        # 视图切换 (示例功能)
        self.view_mode = ctk.CTkSegmentedButton(self.view_tools, values=["原始画面", "SoM网格", "UI匹配"], command=self.change_view_mode)
        self.view_mode.set("原始画面")
        self.view_mode.pack(side="right", padx=10, pady=5)

        # 图片显示区域 (画布)
        self.image_container = ctk.CTkFrame(self.viewport, fg_color="transparent")
        self.image_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.preview_label = ctk.CTkLabel(self.image_container, text="等待画面输入...", text_color="gray")
        self.preview_label.pack(fill="both", expand=True)

    def create_thought_stream(self):
        """右侧日志：思维流"""
        self.thought_stream = ctk.CTkFrame(self, width=350, corner_radius=0)
        self.thought_stream.grid(row=0, column=2, sticky="nsew")
        self.thought_stream.grid_propagate(False)

        # 标题
        title_frame = ctk.CTkFrame(self.thought_stream, height=40, fg_color="#2b2b2b", corner_radius=0)
        title_frame.pack(fill="x", side="top")
        ctk.CTkLabel(title_frame, text="🧠 思维流 (Thought Stream)", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=8)
        
        ctk.CTkButton(title_frame, text="清空", width=50, height=24, fg_color="#555", command=self.clear_logs).pack(side="right", padx=10)

        # 滚动日志区
        self.log_scroll = ctk.CTkScrollableFrame(self.thought_stream, fg_color="transparent")
        self.log_scroll.pack(fill="both", expand=True, padx=5, pady=5)

    # --- 逻辑功能区 ---

    def refresh_game_list(self):
        """加载游戏列表"""
        games = self.knowledge_base.list_games()
        if not games:
            games = ["未找到游戏配置"]
        self.game_selector.configure(values=games)
        self.game_selector.set(games[0])

    def on_game_change(self, choice):
        self.add_log(f"切换目标游戏为: {choice}", type="system")
        self.knowledge_base.load_game(choice)

    def start_agent(self):
        game_name = self.game_selector.get()
        if not game_name or game_name == "未找到游戏配置":
            self.add_log("请先选择有效的游戏配置", type="error")
            return

        self.add_log("正在启动智能代理...", type="system")
        
        # 尝试启动
        # 注意：这里需要根据实际情况获取窗口标题，暂用配置或游戏名
        window_title = self.config_manager.get("game.window_title", game_name)
        
        if self.agent.start(window_title):
            self.status_dot.configure(text_color="#2ecc71") # Green
            self.status_text.configure(text=" 运行中 (Running)")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.add_log(f"代理已连接到窗口: {window_title}", type="system")
        else:
            self.add_log(f"无法连接到游戏窗口: {window_title}", type="error")

    def stop_agent(self):
        self.agent.stop()
        self.status_dot.configure(text_color="red")
        self.status_text.configure(text=" 已停止 (Stopped)")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.add_log("代理已停止", type="system")

    def toggle_debug(self):
        state = self.debug_switch.get()
        self.config_manager.set("debug.enabled", bool(state))
        self.add_log(f"调试模式: {'开启' if state else '关闭'}", type="system")

    def change_view_mode(self, value):
        # 这里需要连接到 agent 的视觉模块来改变输出图像类型
        # 目前仅做日志演示
        self.add_log(f"切换视觉模式: {value}", type="system")

    def update_preview(self, img_array):
        """更新中间视窗的截图"""
        try:
            # 简单缩放适应显示
            img = Image.fromarray(img_array)
            
            # 获取当前显示区域大小
            display_w = self.image_container.winfo_width()
            display_h = self.image_container.winfo_height()
            
            if display_w < 10 or display_h < 10: return

            # 保持比例缩放
            img_ratio = img.width / img.height
            display_ratio = display_w / display_h

            if img_ratio > display_ratio:
                new_w = display_w
                new_h = int(display_w / img_ratio)
            else:
                new_h = display_h
                new_w = int(display_h * img_ratio)

            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            ctk_img = ImageTk.PhotoImage(img)

            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.image = ctk_img
        except Exception as e:
            print(f"Preview Error: {e}")

    # --- 日志系统 ---

    def process_ui_queue(self):
        """处理来自 Agent 的消息"""
        while self.running:
            try:
                msg = self.ui_queue.get(timeout=0.1)
                
                # 如果消息包含图像数据，更新预览
                if "image" in msg:
                    self.master.after(0, self.update_preview, msg["image"])
                
                # 添加日志卡片
                self.master.after(0, self._add_log_card_safe, msg)
                
                self.ui_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Queue Error: {e}")

    def _add_log_card_safe(self, msg):
        """在主线程中安全添加日志卡片"""
        try:
            card = ModernLogCard(
                self.log_scroll, 
                text=msg.get("text", ""), 
                detail=msg.get("detail", ""), 
                type=msg.get("type", "system")
            )
            card.pack(fill="x", pady=2)
            
            # 自动滚动到底部
            self.master.update_idletasks() # 强制刷新计算高度
            self.log_scroll._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def add_log(self, text, detail="", type="system"):
        """手动添加日志的快捷方法"""
        self.ui_queue.put({"text": text, "detail": detail, "type": type})

    def clear_logs(self):
        for widget in self.log_scroll.winfo_children():
            widget.destroy()

    def on_closing(self):
        self.running = False
        self.stop_agent()
        self.destroy()

if __name__ == "__main__":
    app = AICmdCenter()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()