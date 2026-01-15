#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的测试窗口脚本
在主线程中运行，用于测试嵌入功能
"""

import tkinter as tk
from tkinter import ttk
import time

class SimpleTestWindow:
    """简单测试窗口类"""
    
    def __init__(self):
        """初始化测试窗口"""
        self.root = tk.Tk()
        self.root.title("测试嵌入窗口")
        self.root.geometry("400x300")
        self.root.resizable(True, True)
        
        # 设置窗口样式
        style = ttk.Style()
        style.theme_use("clam")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标题
        title_label = ttk.Label(main_frame, text="测试嵌入窗口", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 创建状态文本
        self.status_var = tk.StringVar(value="等待点击...")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(pady=(0, 20))
        
        # 创建测试按钮
        self.button = ttk.Button(
            main_frame, 
            text="点击我", 
            command=self.on_button_click,
            style="Accent.TButton",
            width=20
        )
        self.button.pack(pady=10)
        
        # 添加按钮提示
        hint_label = ttk.Label(main_frame, text="点击此按钮将改变上方文本", font=("Arial", 10, "italic"), foreground="gray")
        hint_label.pack(pady=(0, 20))
        
        # 添加嵌入状态标签
        self.embed_status_var = tk.StringVar(value="当前状态：未嵌入")
        embed_status_label = ttk.Label(main_frame, textvariable=self.embed_status_var, font=("Arial", 10), foreground="blue")
        embed_status_label.pack(pady=(0, 20))
        
        # 定期检查窗口状态
        self.check_embed_status()
    
    def on_button_click(self):
        """按钮点击事件处理"""
        # 改变按钮文本和状态
        current_text = self.button.cget("text")
        if current_text == "点击我":
            self.button.config(text="已点击！")
            self.status_var.set("按钮已被点击！")
        else:
            self.button.config(text="点击我")
            self.status_var.set("等待点击...")
    
    def check_embed_status(self):
        """检查窗口是否被嵌入"""
        try:
            import win32gui
            
            # 获取当前窗口句柄
            hwnd = win32gui.GetParent(self.root.winfo_id())
            
            if hwnd:
                # 窗口已被嵌入
                self.embed_status_var.set(f"当前状态：已嵌入，父窗口句柄：{hwnd}")
            else:
                # 窗口未被嵌入
                self.embed_status_var.set("当前状态：未嵌入")
        except Exception as e:
            self.embed_status_var.set(f"状态检查失败：{str(e)}")
        
        # 每2秒检查一次
        self.root.after(2000, self.check_embed_status)
    
    def run(self):
        """运行窗口主循环"""
        self.root.mainloop()

if __name__ == "__main__":
    # 创建并运行测试窗口
    test_window = SimpleTestWindow()
    test_window.run()