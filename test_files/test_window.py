# -*- coding: utf-8 -*-
"""
简单的测试窗口程序
用于测试脚本点击功能
"""

import tkinter as tk
from tkinter import ttk
import sys

class TestWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("测试窗口")
        self.root.geometry("400x300")
        self.root.resizable(True, True)
        
        # 设置窗口样式
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标题
        title_label = ttk.Label(main_frame, text="测试窗口", font=("微软雅黑", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 添加说明文本
        desc_label = ttk.Label(main_frame, text="这是一个用于测试脚本点击功能的窗口")
        desc_label.pack(pady=(0, 20))
        
        # 添加测试按钮
        self.test_button = ttk.Button(
            main_frame,
            text="测试",
            command=self.on_button_click,
            width=15,
            style="Test.TButton"
        )
        self.test_button.pack(pady=10)
        
        # 添加点击计数
        self.click_count = 0
        self.count_label = ttk.Label(main_frame, text=f"点击次数: {self.click_count}")
        self.count_label.pack(pady=10)
        
        # 添加退出按钮
        quit_button = ttk.Button(main_frame, text="退出", command=root.quit, width=15)
        quit_button.pack(pady=10)
        
        # 设置按钮样式
        self.style.configure("Test.TButton", font=("微软雅黑", 12), padding=10)
    
    def on_button_click(self):
        """按钮点击事件"""
        self.click_count += 1
        self.count_label.config(text=f"点击次数: {self.click_count}")
        print(f"测试按钮被点击，累计次数: {self.click_count}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TestWindow(root)
    root.mainloop()
