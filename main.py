# -*- coding: utf-8 -*-
"""
AI Agent 指挥中心
基于 CustomTkinter 的现代化 UI 框架
参考 Gemini_advice.txt 实现
"""

import customtkinter as ctk
import threading
import queue
import time
import win32gui
import json
import os
from PIL import Image
from datetime import datetime

# 引入核心模块
from smart_agent import SmartAgent
from ai_brain import DoubaoBrain
from config_manager import config_manager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class AICmdCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- 窗口基础设置 ---
        self.title("AI Agent 指挥中心 - Project Daigan")
        self.geometry("1280x800")
        
        # --- 数据通信 ---
        self.log_queue = queue.Queue()
        self.image_queue = queue.Queue()
        self.agent_running = False
        
        # --- 配置管理 ---
        self.config = config_manager.get_config()
        
        # --- 布局初始化 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.init_sidebar()
        self.init_main_area()
        
        # --- 启动 UI 更新循环 ---
        self.after(100, self.update_ui_loop)
    
    def save_config(self):
        """保存配置文件"""
        try:
            if config_manager.save_config(self.config):
                return True
            return False
        except:
            return False
    
    def enum_windows(self):
        """枚举所有可见窗口"""
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
        
        win32gui.EnumWindows(callback, None)
        return windows
    
    def get_games(self):
        """获取knowledge文件夹中的游戏列表"""
        games = []
        knowledge_dir = "knowledge"
        if os.path.exists(knowledge_dir):
            for file in os.listdir(knowledge_dir):
                if file.endswith('.json'):
                    game_name = file.replace('_script.json', '')
                    games.append(game_name)
        return games

    def init_sidebar(self):
        """左侧控制栏"""
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        # 标题
        self.logo_label = ctk.CTkLabel(self.sidebar, text="🤖 AI COMMANDER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=(20, 10))
        
        # 状态指示
        self.status_label = ctk.CTkLabel(self.sidebar, text="● IDLE", text_color="gray", font=("Consolas", 14))
        self.status_label.pack(pady=5)
        
        # 调试模式开关
        self.debug_mode = ctk.BooleanVar(value=False)
        self.debug_switch = ctk.CTkSwitch(self.sidebar, text="🔧 调试模式", variable=self.debug_mode, font=("Consolas", 12))
        self.debug_switch.pack(pady=10, padx=20, fill="x")
        
        # 模式指示灯
        self.mode_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.mode_frame.pack(pady=5)
        
        ctk.CTkLabel(self.mode_frame, text="模式:", font=("Consolas", 12)).pack(side="left", padx=5)
        self.mode_indicator = ctk.CTkLabel(self.mode_frame, text="● 等待中", text_color="gray", font=("Consolas", 12))
        self.mode_indicator.pack(side="left")
        
        # 控制按钮
        self.btn_start = ctk.CTkButton(self.sidebar, text="启动 Agent", fg_color="#2EA043", command=self.start_agent)
        self.btn_start.pack(padx=20, pady=10)
        
        self.btn_stop = ctk.CTkButton(self.sidebar, text="紧急停止 (F12)", fg_color="#DA3633", command=self.stop_agent)
        self.btn_stop.pack(padx=20, pady=10)
        
        # 模式切换
        self.tab_view = ctk.CTkTabview(self.sidebar, height=400)
        self.tab_view.pack(padx=10, pady=20, fill="x")
        self.tab_view.add("监控")
        self.tab_view.add("设置")
        
        # 监控Tab内的快捷指令和指令输入
        self.btn_quick1 = ctk.CTkButton(self.tab_view.tab("监控"), text="测试截图", command=self.test_snapshot)
        self.btn_quick1.pack(pady=5)
        
        # 指令输入
        ctk.CTkLabel(self.tab_view.tab("监控"), text="执行指令:").pack(pady=(10, 5), anchor="w", padx=10)
        self.instruction_var = ctk.StringVar(value="请分析当前界面并做出决策")
        self.instruction_entry = ctk.CTkEntry(self.tab_view.tab("监控"), textvariable=self.instruction_var, width=180)
        self.instruction_entry.pack(pady=5, padx=10)
        
        # 执行按钮
        self.btn_execute = ctk.CTkButton(self.tab_view.tab("监控"), text="执行指令", command=self.execute_instruction)
        self.btn_execute.pack(pady=5)
        
        # 开始循环按钮
        self.btn_loop = ctk.CTkButton(self.tab_view.tab("监控"), text="开始循环", command=self.start_loop)
        self.btn_loop.pack(pady=5)
        
        # 设置Tab内的配置项
        settings_tab = self.tab_view.tab("设置")
        
        # 游戏选择
        ctk.CTkLabel(settings_tab, text="游戏选择:").pack(pady=(10, 5), anchor="w", padx=10)
        games = self.get_games()
        self.game_var = ctk.StringVar(value=self.config.get("selected_game", ""))
        self.game_combo = ctk.CTkComboBox(settings_tab, values=games, variable=self.game_var, width=180)
        self.game_combo.pack(pady=5, padx=10)
        
        # 窗口选择
        ctk.CTkLabel(settings_tab, text="目标窗口:").pack(pady=(10, 5), anchor="w", padx=10)
        windows = self.enum_windows()
        window_values = [f"{hwnd} - {title}" for hwnd, title in windows]
        self.window_var = ctk.StringVar(value=self.config.get("selected_window", ""))
        self.window_combo = ctk.CTkComboBox(settings_tab, values=window_values, variable=self.window_var, width=180)
        self.window_combo.pack(pady=5, padx=10)
        
        # API Key
        ctk.CTkLabel(settings_tab, text="API Key:").pack(pady=(10, 5), anchor="w", padx=10)
        self.api_key_var = ctk.StringVar(value=self.config.get("api_key", ""))
        self.api_key_entry = ctk.CTkEntry(settings_tab, textvariable=self.api_key_var, width=180)
        self.api_key_entry.pack(pady=5, padx=10)
        
        # Endpoint ID
        ctk.CTkLabel(settings_tab, text="Endpoint ID:").pack(pady=(10, 5), anchor="w", padx=10)
        self.endpoint_var = ctk.StringVar(value=self.config.get("endpoint_id", ""))
        self.endpoint_entry = ctk.CTkEntry(settings_tab, textvariable=self.endpoint_var, width=180)
        self.endpoint_entry.pack(pady=5, padx=10)
        
        # 测试API连接按钮
        self.btn_test_api = ctk.CTkButton(settings_tab, text="⚡ 测试连接", command=self.test_api_connection, width=180)
        self.btn_test_api.pack(pady=10, padx=10)
        
        # 测试结果显示
        self.api_test_result = ctk.CTkLabel(settings_tab, text="", font=("Consolas", 12))
        self.api_test_result.pack(pady=5, padx=10)
        
        # 保存配置按钮
        self.btn_save = ctk.CTkButton(settings_tab, text="保存配置", command=self.save_settings, width=180)
        self.btn_save.pack(pady=15, padx=10)
        
        # 刷新窗口列表按钮
        self.btn_refresh = ctk.CTkButton(settings_tab, text="刷新窗口列表", command=self.refresh_windows, width=180)
        self.btn_refresh.pack(pady=5, padx=10)

    def init_main_area(self):
        """右侧主内容区"""
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=3) # 画面占3份
        self.main_frame.grid_columnconfigure(1, weight=2) # 日志占2份
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # 1. 视觉预览区 (The Eye)
        self.preview_frame = ctk.CTkFrame(self.main_frame)
        self.preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        self.preview_label = ctk.CTkLabel(self.preview_frame, text="等待视觉信号...", corner_radius=10)
        self.preview_label.pack(expand=True, fill="both", padx=10, pady=10)
        
        # 2. 思维链日志区 (The Mind)
        self.log_frame = ctk.CTkScrollableFrame(self.main_frame, label_text="思维链日志 (CoT)")
        self.log_frame.grid(row=0, column=1, sticky="nsew")

    def add_log_card(self, text, type="info"):
        """添加卡片式日志"""
        # 检查是否需要显示debug日志
        if (type == "DEBUG" or type == "RAW") and not self.debug_mode.get():
            return
        
        colors = {
            "thought": ("#1c2e4a", "#3b8ed0"), # 深蓝背景
            "action":  ("#1e3a29", "#2cc985"), # 深绿背景
            "error":   ("#4a1c1c", "#fa5a5a"), # 深红背景
            "info":    ("gray20", "gray80"),
            "DEBUG":   ("#2a2a2a", "#a0a0a0"), # 灰色背景
            "RAW":     ("#2a2a2a", "#a0a0a0")  # 灰色背景
        }
        bg, fg = colors.get(type, colors["info"])
        
        card = ctk.CTkFrame(self.log_frame, fg_color=bg)
        card.pack(fill="x", pady=2, padx=5)
        
        ts = datetime.now().strftime("%H:%M:%S")
        
        # 标题行
        header = ctk.CTkLabel(card, text=f"[{ts}] {type.upper()}", text_color=fg, font=("Arial", 10, "bold"), anchor="w")
        header.pack(fill="x", padx=5, pady=(5,0))
        
        # 内容行 - debug日志使用灰色等宽字体
        if type in ["DEBUG", "RAW"]:
            content = ctk.CTkLabel(card, text=text, text_color="#a0a0a0", font=("Consolas", 11), justify="left", anchor="w", wraplength=300)
        else:
            content = ctk.CTkLabel(card, text=text, text_color="white", font=("Consolas", 12), justify="left", anchor="w", wraplength=300)
        content.pack(fill="x", padx=5, pady=(0,5))
        
        # 自动滚动到底部
        self.log_frame._parent_canvas.yview_moveto(1.0)

    def update_image_preview(self, pil_image):
        """更新视觉预览，处理图片尺寸适配"""
        # 计算缩放
        w_box = self.preview_frame.winfo_width()
        h_box = self.preview_frame.winfo_height()
        
        # 简单的保持比例缩放逻辑
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(w_box-20, h_box-20))
        self.preview_label.configure(image=ctk_img, text="")

    def update_ui_loop(self):
        """UI 主循环，处理队列消息"""
        # 1. 处理日志
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.add_log_card(msg['text'], msg['type'])
                
                # 更新模式指示灯
                text = msg.get('text', '')
                if '快系统' in text:
                    self.mode_indicator.configure(text="● 缓存模式", text_color="#2cc985")
                elif '慢系统' in text:
                    self.mode_indicator.configure(text="● 思考模式", text_color="#3b8ed0")
                elif '异步写入缓存' in text or '缓存写入成功' in text:
                    self.mode_indicator.configure(text="● 更新图谱", text_color="#f9ca24")
        except queue.Empty:
            pass
        
        # 2. 处理图像
        try:
            while True:
                # 只取最新的一张图，丢弃旧的以防卡顿
                img = self.image_queue.get_nowait()
                if self.image_queue.empty():
                    self.update_image_preview(img)
        except queue.Empty:
            pass
            
        self.after(100, self.update_ui_loop)

    # --- 核心控制功能 ---
    def start_agent(self):
        self.status_label.configure(text="● RUNNING", text_color="#2cc985")
        self.log_queue.put({"text": "Agent 启动初始化...", "type": "info"})
        
        # 启动 agent_core 线程
        def agent_thread():
            try:
                from smart_agent import SmartAgent
                from ai_brain import DoubaoBrain
                from knowledge_manager import KnowledgeBase
                
                # 获取选择的窗口
                selected_window = self.window_var.get()
                if selected_window:
                    # 解析窗口句柄
                    hwnd_str = selected_window.split(" - ")[0]
                    hwnd = int(hwnd_str)
                    self.log_queue.put({"text": f"正在连接窗口: {hwnd}", "type": "info"})
                else:
                    # 无窗口选择时的默认初始化
                    self.log_queue.put({"text": "未选择窗口，使用默认初始化", "type": "info"})
                    hwnd = None
                
                # 获取 API 配置
                api_key = self.api_key_var.get()
                endpoint_id = self.endpoint_var.get()
                
                # 初始化知识库
                knowledge_base = KnowledgeBase()
                selected_game = self.game_var.get()
                if selected_game:
                    load_success = knowledge_base.load_game(selected_game)
                    if load_success:
                        self.log_queue.put({"text": f"成功加载游戏知识库: {selected_game}", "type": "info"})
                    else:
                        self.log_queue.put({"text": f"加载游戏知识库失败: {selected_game}", "type": "warning"})
                else:
                    self.log_queue.put({"text": "未选择游戏，使用空知识库", "type": "info"})
                
                ai_brain = DoubaoBrain(api_key=api_key, endpoint_id=endpoint_id, ui_queue=self.log_queue)
                
                self.agent = SmartAgent(
                    hwnd=hwnd,
                    ai_brain=ai_brain,
                    ui_queue=self.log_queue,
                    img_queue=self.image_queue,
                    knowledge_base=knowledge_base
                )
                
                self.agent_running = True
                self.log_queue.put({"text": "Agent 启动成功！", "type": "info"})
                
            except Exception as e:
                self.log_queue.put({"text": f"Agent 启动失败: {str(e)}", "type": "error"})
                self.status_label.configure(text="● ERROR", text_color="#fa5a5a")
        
        threading.Thread(target=agent_thread, daemon=True).start()

    def stop_agent(self):
        self.status_label.configure(text="● STOPPED", text_color="#fa5a5a")
        self.log_queue.put({"text": "用户触发紧急停止", "type": "error"})
        
        if hasattr(self, 'agent'):
            self.agent_running = False
            # 清理 agent 资源
            del self.agent

    def test_snapshot(self):
        """测试用：获取真实屏幕截图"""
        self.log_queue.put({"text": "正在获取屏幕截图...", "type": "thought"})
        
        # 获取选中的窗口
        selected_window = self.window_var.get()
        if not selected_window:
            self.log_queue.put({"text": "未选择窗口，请先选择目标窗口", "type": "error"})
            return
        
        try:
            # 解析窗口句柄
            hwnd_str = selected_window.split(" - ")[0]
            hwnd = int(hwnd_str)
            
            # 实例化GameWindow
            from game_window import GameWindow
            window = GameWindow()
            window.init_hwnd(hwnd)
            
            # 获取真实截图
            img = window.snapshot()
            if img:
                self.log_queue.put({"text": "成功获取屏幕截图", "type": "action"})
                self.image_queue.put(img)
            else:
                self.log_queue.put({"text": "截图失败，请检查窗口是否正常", "type": "error"})
        except Exception as e:
            self.log_queue.put({"text": f"截图异常: {str(e)}", "type": "error"})
    
    def save_settings(self):
        """保存设置"""
        self.config["selected_game"] = self.game_var.get()
        self.config["selected_window"] = self.window_var.get()
        self.config["api_key"] = self.api_key_var.get()
        self.config["endpoint_id"] = self.endpoint_var.get()
        
        if self.save_config():
            self.log_queue.put({"text": "配置保存成功", "type": "info"})
        else:
            self.log_queue.put({"text": "配置保存失败", "type": "error"})
    
    def refresh_windows(self):
        """刷新窗口列表"""
        windows = self.enum_windows()
        window_values = [f"{hwnd} - {title}" for hwnd, title in windows]
        self.window_combo.configure(values=window_values)
        self.log_queue.put({"text": "窗口列表已刷新", "type": "info"})
    
    def test_api_connection(self):
        """测试API连接"""
        # 获取API配置
        api_key = self.api_key_var.get()
        endpoint_id = self.endpoint_var.get()
        
        if not api_key or not endpoint_id:
            self.api_test_result.configure(text="❌ 请先填写API Key和Endpoint ID", text_color="#fa5a5a")
            return
        
        # 禁用按钮并显示测试中
        self.btn_test_api.configure(text="Testing...", state="disabled")
        self.api_test_result.configure(text="测试中...", text_color="#f9ca24")
        
        # 在单独线程中执行测试
        def test_thread():
            try:
                from ai_brain import DoubaoBrain
                brain = DoubaoBrain(api_key=api_key, endpoint_id=endpoint_id, ui_queue=self.log_queue)
                is_success, latency_ms, message = brain.test_connection_speed()
                
                # 更新UI
                if is_success:
                    self.api_test_result.configure(text=f"✅ 成功 {latency_ms}ms", text_color="#2cc985")
                    self.log_queue.put({"text": f"API连接测试成功，延迟: {latency_ms}ms", "type": "info"})
                else:
                    self.api_test_result.configure(text=f"❌ 失败: {message}", text_color="#fa5a5a")
                    self.log_queue.put({"text": f"API连接测试失败: {message}", "type": "error"})
            except Exception as e:
                self.api_test_result.configure(text=f"❌ 异常: {str(e)}", text_color="#fa5a5a")
                self.log_queue.put({"text": f"API测试异常: {str(e)}", "type": "error"})
            finally:
                # 恢复按钮状态
                self.btn_test_api.configure(text="⚡ 测试连接", state="normal")
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def execute_instruction(self):
        """执行单次指令"""
        if not hasattr(self, 'agent'):
            self.log_queue.put({"text": "Agent 未初始化，请先启动", "type": "error"})
            return
        
        instruction = self.instruction_var.get()
        if not instruction:
            self.log_queue.put({"text": "请输入执行指令", "type": "error"})
            return
        
        self.log_queue.put({"text": f"执行指令: {instruction}", "type": "info"})
        
        # 在单独线程中执行，避免阻塞UI
        def execute_thread():
            try:
                result = self.agent.step(instruction)
                if result:
                    if result.get("success"):
                        self.log_queue.put({"text": f"执行成功: {result.get('message', '')}", "type": "info"})
                    else:
                        self.log_queue.put({"text": f"执行失败: {result.get('message', '')}", "type": "error"})
                else:
                    self.log_queue.put({"text": "执行无结果", "type": "error"})
            except Exception as e:
                self.log_queue.put({"text": f"执行异常: {str(e)}", "type": "error"})
        
        threading.Thread(target=execute_thread, daemon=True).start()
    
    def start_loop(self):
        """开始循环执行指令"""
        if not hasattr(self, 'agent'):
            self.log_queue.put({"text": "Agent 未初始化，请先启动", "type": "error"})
            return
        
        instruction = self.instruction_var.get()
        if not instruction:
            self.log_queue.put({"text": "请输入执行指令", "type": "error"})
            return
        
        self.log_queue.put({"text": f"开始循环执行指令: {instruction}", "type": "info"})
        
        # 在单独线程中执行，避免阻塞UI
        def loop_thread():
            try:
                result = self.agent.run_loop(instruction)
                if result:
                    self.log_queue.put({"text": "循环执行完成", "type": "info"})
                else:
                    self.log_queue.put({"text": "循环执行失败", "type": "error"})
            except Exception as e:
                self.log_queue.put({"text": f"循环执行异常: {str(e)}", "type": "error"})
        
        threading.Thread(target=loop_thread, daemon=True).start()


if __name__ == "__main__":
    # 初始化 config_manager
    config_manager
    
    # 启动应用
    app = AICmdCenter()
    app.mainloop()
