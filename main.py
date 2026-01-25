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
from ai_brain import AIBrain # 用于测试连接

# 设置外观模式
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# ============================================================================
# 组件类定义
# ============================================================================

class SettingsDialog(ctk.CTkToplevel):
    """
    设置弹窗：用于配置 API Key 和 模型参数
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config = ConfigManager()
        
        # 窗口设置
        self.title("系统设置 (Settings)")
        self.geometry("500x450")
        self.resizable(False, False)
        self.attributes("-topmost", True) # 置顶
        
        # 居中显示
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - 250
        y = parent.winfo_y() + (parent.winfo_height() // 2) - 225
        self.geometry(f"+{x}+{y}")

        self.create_widgets()
        self.load_current_config()

    def create_widgets(self):
        # 标题
        ctk.CTkLabel(self, text="AI 模型配置", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 10))

        # 表单区域
        self.form_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.form_frame.pack(fill="both", expand=True, padx=30)

        # 1. API Key
        ctk.CTkLabel(self.form_frame, text="API Key:", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_key = ctk.CTkEntry(self.form_frame, placeholder_text="sk-xxxxxxxx", show="*")
        self.entry_key.pack(fill="x", pady=5)
        
        # 显示/隐藏 密码的开关
        self.show_key = ctk.CTkCheckBox(self.form_frame, text="显示 API Key", command=self.toggle_key_visibility, font=ctk.CTkFont(size=12))
        self.show_key.pack(anchor="w", pady=(0, 10))

        # 2. Endpoint ID (火山引擎/豆包特有)
        ctk.CTkLabel(self.form_frame, text="Endpoint ID (火山引擎节点号):", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_endpoint = ctk.CTkEntry(self.form_frame, placeholder_text="ep-2024xxxx-xxxxx")
        self.entry_endpoint.pack(fill="x", pady=5)

        # 3. Model Name
        ctk.CTkLabel(self.form_frame, text="Model Name (模型名称):", anchor="w").pack(fill="x", pady=(10, 0))
        self.entry_model = ctk.CTkOptionMenu(self.form_frame, values=["doubao-pro-4k", "doubao-lite-4k", "gpt-4o", "custom"])
        self.entry_model.pack(fill="x", pady=5)

        # 测试结果显示区
        self.lbl_status = ctk.CTkLabel(self.form_frame, text="", text_color="gray")
        self.lbl_status.pack(pady=10)

        # 按钮区域
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=20, side="bottom")

        self.btn_test = ctk.CTkButton(btn_frame, text="⚡ 测试连接", fg_color="#e67e22", hover_color="#d35400", command=self.test_connection)
        self.btn_test.pack(side="left", expand=True, fill="x", padx=(0, 10))

        self.btn_save = ctk.CTkButton(btn_frame, text="💾 保存配置", fg_color="#27ae60", hover_color="#2ecc71", command=self.save_config)
        self.btn_save.pack(side="right", expand=True, fill="x", padx=(10, 0))

    def load_current_config(self):
        """加载当前配置到输入框"""
        self.entry_key.insert(0, self.config.get("ai.api_key", ""))
        self.entry_endpoint.insert(0, self.config.get("ai.endpoint_id", ""))
        current_model = self.config.get("ai.model", "doubao-pro-4k")
        self.entry_model.set(current_model)

    def toggle_key_visibility(self):
        if self.show_key.get():
            self.entry_key.configure(show="")
        else:
            self.entry_key.configure(show="*")

    def test_connection(self):
        """测试 API 连接"""
        api_key = self.entry_key.get().strip()
        endpoint = self.entry_endpoint.get().strip()
        
        if not api_key:
            self.lbl_status.configure(text="❌ 请先输入 API Key", text_color="#e74c3c")
            return

        self.lbl_status.configure(text="⏳ 正在连接 AI 大脑...", text_color="#f1c40f")
        self.btn_test.configure(state="disabled")
        
        # 在新线程中测试，防止界面卡死
        threading.Thread(target=self._run_test, args=(api_key, endpoint)).start()

    def _run_test(self, api_key, endpoint):
        try:
            # 临时保存一下配置以便 AIBrain 读取（或者修改 AIBrain 支持传参）
            # 这里我们假设 AIBrain 初始化时会读取 config
            # 为了测试安全，我们先临时实例化一个 AIBrain
            
            # 注意：这里需要确保 ConfigManager 在内存中更新，或者临时传递参数
            # 由于 AIBrain 内部是通过 ConfigManager().get() 读取的，
            # 我们先临时写入 Config (不保存到文件)，测试完再决定是否保存
            
            temp_config = ConfigManager()
            temp_config.set("ai.api_key", api_key)
            temp_config.set("ai.endpoint_id", endpoint)
            
            brain = AIBrain()
            # 发送一个极简的测试 Prompt
            result = brain.get_advice("这是一个API连接测试，请回复'OK'。")
            
            if result.get("success"):
                self.parent.after(0, lambda: self._update_status("✅ 连接成功！AI回复: " + result["data"]["advice"][:20], "#2ecc71"))
            else:
                error_msg = result.get("error", "未知错误")
                self.parent.after(0, lambda: self._update_status(f"❌ 连接失败: {error_msg}", "#e74c3c"))
                
        except Exception as e:
            self.parent.after(0, lambda: self._update_status(f"❌ 程序异常: {str(e)}", "#e74c3c"))
        finally:
            self.parent.after(0, lambda: self.btn_test.configure(state="normal"))

    def _update_status(self, text, color):
        self.lbl_status.configure(text=text, text_color=color)

    def save_config(self):
        """保存配置到文件"""
        self.config.set("ai.api_key", self.entry_key.get().strip())
        self.config.set("ai.endpoint_id", self.entry_endpoint.get().strip())
        self.config.set("ai.model", self.entry_model.get())
        
        # 通知主界面
        self.parent.add_log("系统配置已更新", type="SYSTEM")
        self.destroy()


class ModernLogCard(ctk.CTkFrame):
    """双层结构日志卡片"""
    COLORS = {
        "THOUGHT": "#9b59b6", "VISION": "#3498db", "ACTION": "#2ecc71", 
        "SYSTEM": "#95a5a6", "ERROR": "#e74c3c"
    }
    ICONS = {
        "THOUGHT": "🧠", "VISION": "👁️", "ACTION": "🖱️", 
        "SYSTEM": "⚙️", "ERROR": "❌"
    }

    def __init__(self, master, log_data: dict, **kwargs):
        super().__init__(master, fg_color="#2b2b2b", corner_radius=6, **kwargs)
        raw_type = log_data.get("type", "SYSTEM")
        self.type = raw_type.upper() if raw_type else "SYSTEM"
        self.text = log_data.get("text", "Info")
        self.detail = log_data.get("detail", "")
        ts = log_data.get("time", time.time())
        self.timestamp = time.strftime("%H:%M:%S", time.localtime(ts))
        
        self.is_expanded = False
        accent_color = self.COLORS.get(self.type, "#95a5a6")
        icon = self.ICONS.get(self.type, "📝")

        self.bar = ctk.CTkFrame(self, width=4, fg_color=accent_color, corner_radius=0)
        self.bar.pack(side="left", fill="y", padx=(0, 5))

        self.content_box = ctk.CTkFrame(self, fg_color="transparent")
        self.content_box.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.header_frame = ctk.CTkFrame(self.content_box, fg_color="transparent")
        self.header_frame.pack(fill="x")
        self.header_frame.bind("<Button-1>", self.toggle_expand)

        title_text = f"[{self.timestamp}] {icon} {self.text}"
        self.info_label = ctk.CTkLabel(self.header_frame, text=title_text, font=ctk.CTkFont(size=12, weight="bold"), anchor="w", text_color="#ecf0f1")
        self.info_label.pack(side="left", fill="x", expand=True)
        self.info_label.bind("<Button-1>", self.toggle_expand)

        if self.detail:
            self.expand_btn = ctk.CTkLabel(self.header_frame, text="▼", width=20, text_color="#7f8c8d", font=ctk.CTkFont(size=10))
            self.expand_btn.pack(side="right")
            self.expand_btn.bind("<Button-1>", self.toggle_expand)
            
            self.detail_text = ctk.CTkTextbox(self.content_box, height=0, fg_color="#1e1e1e", text_color="#bdc3c7", font=ctk.CTkFont(family="Consolas", size=11), activate_scrollbars=False)
            self.detail_text.insert("0.0", str(self.detail))
            self.detail_text.configure(state="disabled")

    def toggle_expand(self, event=None):
        if not self.detail: return
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.expand_btn.configure(text="▲")
            self.detail_text.pack(fill="x", pady=(5, 0))
            try:
                line_count = int(self.detail_text.index('end-1c').split('.')[0])
                new_height = min(200, max(60, line_count * 16))
            except: new_height = 100
            self.detail_text.configure(height=new_height, activate_scrollbars=True)
        else:
            self.expand_btn.configure(text="▼")
            self.detail_text.pack_forget()
            self.detail_text.configure(height=0)

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
        card = ModernLogCard(self.scroll_frame, log_data)
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
# 主窗口类
# ============================================================================

class AICmdCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AI Game Agent - Command Center")
        self.geometry("1280x800")
        self.minsize(1000, 700)
        
        self.config_manager = ConfigManager()
        self.knowledge_base = KnowledgeBase()
        self.ui_queue = queue.Queue()
        self.agent = SmartAgent(ui_queue=self.ui_queue)
        
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_viewport()
        self.create_thought_stream()
        
        self.running = True
        self.log_thread = threading.Thread(target=self.process_ui_queue, daemon=True)
        self.log_thread.start()
        
        self.refresh_game_list()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(self.sidebar, text="🤖 AI AGENT", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(20, 10))
        ctk.CTkLabel(self.sidebar, text="v1.0.0", text_color="gray").pack(pady=(0, 20))

        ctk.CTkLabel(self.sidebar, text="目标游戏 (Target Game)", anchor="w").pack(fill="x", padx=20, pady=(10, 0))
        self.game_selector = ctk.CTkOptionMenu(self.sidebar, dynamic_resizing=False, command=self.on_game_change)
        self.game_selector.pack(fill="x", padx=20, pady=5)

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.pack(fill="x", padx=20, pady=20)
        self.status_dot = ctk.CTkLabel(self.status_frame, text="●", text_color="red", font=("Arial", 24))
        self.status_dot.pack(side="left")
        self.status_text = ctk.CTkLabel(self.status_frame, text=" 已停止 (Stopped)", anchor="w")
        self.status_text.pack(side="left", padx=10)

        self.btn_start = ctk.CTkButton(self.sidebar, text="▶ 启动代理 (START)", fg_color="#27ae60", hover_color="#2ecc71", height=40, font=ctk.CTkFont(weight="bold"), command=self.start_agent)
        self.btn_start.pack(fill="x", padx=20, pady=(10, 5))

        self.btn_stop = ctk.CTkButton(self.sidebar, text="⏹ 停止代理 (STOP)", fg_color="#c0392b", hover_color="#e74c3c", height=40, font=ctk.CTkFont(weight="bold"), state="disabled", command=self.stop_agent)
        self.btn_stop.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(self.sidebar, text="调试工具", anchor="w").pack(fill="x", padx=20, pady=(30, 0))
        self.debug_switch = ctk.CTkSwitch(self.sidebar, text="调试模式 (Debug Mode)", command=self.toggle_debug)
        self.debug_switch.pack(fill="x", padx=20, pady=10)
        if self.config_manager.get("debug.enabled"): self.debug_switch.select()

        # --- 新增：底部设置按钮 ---
        self.btn_settings = ctk.CTkButton(self.sidebar, text="⚙️ 系统配置 (Settings)", fg_color="#2c3e50", hover_color="#34495e", command=self.open_settings)
        self.btn_settings.pack(side="bottom", fill="x", padx=20, pady=20)

    def create_viewport(self):
        self.viewport = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=0)
        self.viewport.grid(row=0, column=1, sticky="nsew", padx=2)
        
        self.view_tools = ctk.CTkFrame(self.viewport, height=40, fg_color="#2b2b2b")
        self.view_tools.pack(fill="x", side="top")
        
        ctk.CTkLabel(self.view_tools, text=" 👁️ 视觉感知 (Visual Perception) ", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.view_mode = ctk.CTkSegmentedButton(self.view_tools, values=["原始画面", "SoM网格", "UI匹配"], command=self.change_view_mode)
        self.view_mode.set("原始画面")
        self.view_mode.pack(side="right", padx=10, pady=5)

        self.image_container = ctk.CTkFrame(self.viewport, fg_color="transparent")
        self.image_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.preview_label = ctk.CTkLabel(self.image_container, text="等待画面输入...", text_color="gray")
        self.preview_label.pack(fill="both", expand=True)

    def create_thought_stream(self):
        self.thought_panel = ThoughtStreamPanel(self, width=380, corner_radius=0)
        self.thought_panel.grid(row=0, column=2, sticky="nsew")
        self.thought_panel.grid_propagate(False)

    # --- 功能逻辑 ---

    def open_settings(self):
        """打开设置弹窗"""
        SettingsDialog(self)

    def refresh_game_list(self):
        games = self.knowledge_base.list_games()
        if not games: games = ["未找到游戏配置"]
        self.game_selector.configure(values=games)
        self.game_selector.set(games[0])

    def on_game_change(self, choice):
        self.add_log(f"切换目标游戏为: {choice}", type="SYSTEM")
        self.knowledge_base.load_game(choice)

    def start_agent(self):
        game_name = self.game_selector.get()
        if not game_name or game_name == "未找到游戏配置":
            self.add_log("请先选择有效的游戏配置", type="ERROR")
            return
        self.add_log("正在启动智能代理...", type="SYSTEM")
        window_title = self.config_manager.get("game.window_title", game_name)
        if self.agent.start(window_title):
            self.status_dot.configure(text_color="#2ecc71")
            self.status_text.configure(text=" 运行中 (Running)")
            self.btn_start.configure(state="disabled")
            self.btn_stop.configure(state="normal")
            self.add_log(f"代理已连接到窗口: {window_title}", type="SYSTEM")
        else:
            self.add_log(f"无法连接到游戏窗口: {window_title}", type="ERROR")

    def stop_agent(self):
        self.agent.stop()
        self.status_dot.configure(text_color="red")
        self.status_text.configure(text=" 已停止 (Stopped)")
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.add_log("代理已停止", type="SYSTEM")

    def toggle_debug(self):
        state = self.debug_switch.get()
        self.config_manager.set("debug.enabled", bool(state))
        self.add_log(f"调试模式: {'开启' if state else '关闭'}", type="SYSTEM")

    def change_view_mode(self, value):
        self.add_log(f"切换视觉模式: {value}", type="SYSTEM")

    def update_preview(self, img_array):
        try:
            img = Image.fromarray(img_array)
            display_w = self.image_container.winfo_width()
            display_h = self.image_container.winfo_height()
            if display_w < 10 or display_h < 10: return
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
        except Exception as e: print(f"Preview Error: {e}")

    def process_ui_queue(self):
        while self.running:
            try:
                msg = self.ui_queue.get(timeout=0.1)
                if "image" in msg: self.master.after(0, self.update_preview, msg["image"])
                self.master.after(0, self._add_log_card_safe, msg)
                self.ui_queue.task_done()
            except queue.Empty: continue
            except Exception as e: print(f"Queue Error: {e}")

    def _add_log_card_safe(self, msg):
        try: self.thought_panel.add_log(msg)
        except Exception: pass

    def add_log(self, text, detail="", type="SYSTEM"):
        self.ui_queue.put({"text": text, "detail": detail, "type": type})

    def clear_logs(self):
        self.thought_panel.clear()

    def on_closing(self):
        self.running = False
        self.stop_agent()
        self.destroy()

if __name__ == "__main__":
    app = AICmdCenter()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()