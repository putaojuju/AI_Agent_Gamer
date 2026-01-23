# -*- coding: utf-8 -*-
"""
AI Agent 控制台
基于 ReAct 架构的游戏自动化 Agent 控制台
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import os
import logging

log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'agent_console.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent_console')


class AgentConsole:
    """
    AI Agent 控制台类
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 AI Agent 控制台")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        self.agent = None
        self.log_queue = queue.Queue()
        self.is_running = False
        
        self.game_var = tk.StringVar()
        self.api_key_var = tk.StringVar()
        self.endpoint_var = tk.StringVar()
        self.base_url_var = tk.StringVar(value="https://ark.cn-beijing.volces.com/api/v3")
        
        self.setup_styles()
        self.create_widgets()
        self.load_games()
        self.load_config()
        self.update_logs()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置样式
        style.configure("TButton", font=('微软雅黑', 10), padding=8)
        style.configure("Primary.TButton", font=('微软雅黑', 11, 'bold'), foreground='#007acc', padding=10)
        style.configure("Danger.TButton", font=('微软雅黑', 11, 'bold'), foreground='#dc3545', padding=10)
        style.configure("Header.TLabel", font=('微软雅黑', 16, 'bold'), background='#ffffff', foreground='#333333')
        style.configure("Section.TLabel", font=('微软雅黑', 12, 'bold'), background='#f5f5f5', foreground='#333333')
        style.configure("TFrame", background='#f5f5f5')
        style.configure("Card.TFrame", background='#ffffff', relief='flat')
        
        # 配置日志文本样式
        style.configure("Log.TText", font=('Consolas', 10), background='#1e1e1e', foreground='#d4d4d4')
    
    def create_widgets(self):
        # 主容器
        main_container = ttk.Frame(self.root, style="TFrame")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 顶部标题栏
        self.create_header(main_container)
        
        # 内容区域
        content_area = ttk.Frame(main_container, style="TFrame", padding=20)
        content_area.pack(fill=tk.BOTH, expand=True)
        
        # 配置区域
        config_frame = ttk.Frame(content_area, style="Card.TFrame", padding=15)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(config_frame, text="🎮 游戏配置", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        # 游戏选择
        game_row = ttk.Frame(config_frame, style="Card.TFrame")
        game_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(game_row, text="选择游戏:").pack(side=tk.LEFT, padx=(0, 10))
        self.game_combo = ttk.Combobox(game_row, textvariable=self.game_var, state="readonly", width=30)
        self.game_combo.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(game_row, text="🔄 刷新", command=self.load_games, style="TButton").pack(side=tk.LEFT)
        
        # AI 配置
        ttk.Label(config_frame, text="🧠 AI 配置", style="Section.TLabel").pack(anchor=tk.W, pady=(20, 10))
        
        ttk.Label(config_frame, text="火山引擎 API Key:").pack(anchor=tk.W)
        ttk.Entry(config_frame, textvariable=self.api_key_var, show="*", width=60).pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="模型端点 ID (Endpoint ID):").pack(anchor=tk.W)
        ttk.Entry(config_frame, textvariable=self.endpoint_var, width=60).pack(fill=tk.X, pady=5)
        
        ttk.Label(config_frame, text="API 基础 URL:").pack(anchor=tk.W)
        ttk.Entry(config_frame, textvariable=self.base_url_var, width=60).pack(fill=tk.X, pady=(5, 15))
        
        # 操作按钮
        button_row = ttk.Frame(config_frame, style="Card.TFrame")
        button_row.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_row, text="🔗 连接 Agent", command=self.connect_agent, style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row, text="💾 保存配置", command=self.save_config, style="TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_row, text="❌ 断开连接", command=self.disconnect_agent, style="Danger.TButton").pack(side=tk.LEFT)
        
        # 指令输入区域
        input_frame = ttk.Frame(content_area, style="Card.TFrame", padding=15)
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(input_frame, text="💬 指令输入", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.instruction_entry = ttk.Entry(input_frame, font=('微软雅黑', 11), width=80)
        self.instruction_entry.pack(fill=tk.X, pady=5)
        self.instruction_entry.bind('<Return>', lambda e: self.execute_instruction())
        
        exec_row = ttk.Frame(input_frame, style="Card.TFrame")
        exec_row.pack(fill=tk.X, pady=5)
        
        ttk.Button(exec_row, text="▶ 执行指令", command=self.execute_instruction, style="Primary.TButton").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(exec_row, text="🧹 清空日志", command=self.clear_logs, style="TButton").pack(side=tk.LEFT)
        
        # 日志显示区域
        log_frame = ttk.Frame(content_area, style="Card.TFrame", padding=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        ttk.Label(log_frame, text="📝 思维链日志", style="Section.TLabel").pack(anchor=tk.W, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#d4d4d4',
            wrap=tk.WORD,
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self._configure_log_tags()
    
    def create_header(self, parent):
        header = ttk.Frame(parent, style="Card.TFrame", padding=(20, 15))
        header.pack(fill=tk.X)
        
        ttk.Label(header, text="🤖 AI Agent 控制台", style="Header.TLabel").pack(side=tk.LEFT)
        
        self.status_label = ttk.Label(header, text="● 未连接", foreground="gray", font=('微软雅黑', 10))
        self.status_label.pack(side=tk.RIGHT)
    
    def _configure_log_tags(self):
        self.log_text.tag_config("timestamp", foreground="#666666", font=("Consolas", 9))
        self.log_text.tag_config("THOUGHT", foreground="#9b59b6", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("ACTION", foreground="#e67e22", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("OBSERVATION", foreground="#3498db", font=("微软雅黑", 10))
        self.log_text.tag_config("SUCCESS", foreground="#28a745", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("ERROR", foreground="#dc3545", font=("微软雅黑", 10, "bold"))
        self.log_text.tag_config("INFO", foreground="#7f8c8d", font=("微软雅黑", 10))
    
    def load_games(self):
        from knowledge_manager import KnowledgeBase
        
        kb = KnowledgeBase()
        games = kb.list_games()
        
        self.game_combo['values'] = games
        
        if games:
            self.log(f"📂 已加载 {len(games)} 个游戏知识库: {', '.join(games)}", "INFO")
        else:
            self.log("⚠️  未找到任何游戏知识库，请在 knowledge/ 目录下创建 JSON 文件", "ERROR")
    
    def connect_agent(self):
        game_name = self.game_var.get()
        api_key = self.api_key_var.get()
        endpoint_id = self.endpoint_var.get()
        base_url = self.base_url_var.get()
        
        if not game_name:
            messagebox.showwarning("提示", "请先选择一个游戏")
            return
        
        if not api_key or not endpoint_id:
            messagebox.showwarning("提示", "请填写 API Key 和 Endpoint ID")
            return
        
        try:
            self.log(f"🔗 正在连接 Agent (游戏: {game_name})...", "INFO")
            
            from agent_core import GameAgent
            
            self.agent = GameAgent(
                game_name=game_name,
                api_key=api_key,
                endpoint_id=endpoint_id,
                base_url=base_url
            )
            
            self.is_running = True
            self.status_label.config(text="● 已连接", foreground="green")
            self.log(f"✅ Agent 连接成功！当前游戏: {game_name}", "SUCCESS")
            
            # 显示知识库信息
            keys = self.agent.get_all_keys()
            self.log(f"📚 已加载 {len(keys)} 条知识", "INFO")
            
        except Exception as e:
            self.log(f"❌ 连接 Agent 失败: {e}", "ERROR")
            messagebox.showerror("错误", f"连接失败: {e}")
    
    def disconnect_agent(self):
        if self.agent:
            self.agent = None
            self.is_running = False
            self.status_label.config(text="● 未连接", foreground="gray")
            self.log("🔌 Agent 已断开连接", "INFO")
    
    def execute_instruction(self):
        instruction = self.instruction_entry.get().strip()
        
        if not instruction:
            messagebox.showwarning("提示", "请输入指令")
            return
        
        if not self.agent:
            messagebox.showwarning("提示", "请先连接 Agent")
            return
        
        self.log(f"📤 执行指令: {instruction}", "INFO")
        
        thread = threading.Thread(
            target=self._execute_in_thread,
            args=(instruction,),
            daemon=True
        )
        thread.start()
        
        self.instruction_entry.delete(0, tk.END)
    
    def _execute_in_thread(self, instruction):
        try:
            result = self.agent.run(instruction)
            self.log(f"✅ 执行完成: {result}", "SUCCESS")
        except Exception as e:
            self.log(f"❌ 执行失败: {e}", "ERROR")
    
    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log(self, message, level="INFO"):
        self.log_queue.put((message, level))
        if level == "ERROR":
            logger.error(message)
        elif level == "SUCCESS":
            logger.info(message)
        else:
            logger.info(message)
    
    def update_logs(self):
        while not self.log_queue.empty():
            message, level = self.log_queue.get()
            
            self.log_text.config(state=tk.NORMAL)
            
            timestamp = f"[{self._get_timestamp()}] "
            self.log_text.insert(tk.END, timestamp, "timestamp")
            
            tag = level
            self.log_text.insert(tk.END, message + "\n", tag)
            
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(100, self.update_logs)
    
    def _get_timestamp(self):
        import time
        return time.strftime("%H:%M:%S")
    
    def load_config(self):
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.game_var.set(config.get('game', ''))
                    self.api_key_var.set(config.get('api_key', ''))
                    self.endpoint_var.set(config.get('endpoint_id', ''))
                    self.base_url_var.set(config.get('base_url', 'https://ark.cn-beijing.volces.com/api/v3'))
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
    
    def save_config(self):
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_config.json")
            import json
            config = {
                'game': self.game_var.get(),
                'api_key': self.api_key_var.get(),
                'endpoint_id': self.endpoint_var.get(),
                'base_url': self.base_url_var.get()
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("成功", "配置已保存")
            self.log("✅ 配置已保存", "SUCCESS")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败: {e}")
            self.log(f"❌ 保存配置失败: {e}", "ERROR")


if __name__ == "__main__":
    root = tk.Tk()
    app = AgentConsole(root)
    root.mainloop()
