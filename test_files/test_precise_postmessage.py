# -*- coding: utf-8 -*-
"""
精确的PostMessage测试脚本
直接发送消息到测试窗口的客户区，确保点击到按钮
"""

import win32gui
import win32con
import time
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def main():
    """主函数"""
    print("=" * 60)
    print("精确的PostMessage测试脚本")
    print("=" * 60)
    
    # 获取测试窗口句柄
    window_title = "测试窗口"
    hwnd = win32gui.FindWindow(None, window_title)
    
    if hwnd == 0:
        print(f"错误：未找到窗口标题为 '{window_title}' 的窗口")
        return
    
    print(f"找到窗口句柄：{hwnd}")
    print(f"窗口标题：{win32gui.GetWindowText(hwnd)}")
    
    # 获取窗口位置和大小
    window_rect = win32gui.GetWindowRect(hwnd)
    print(f"窗口矩形：{window_rect}")
    
    # 获取客户区大小
    client_rect = win32gui.GetClientRect(hwnd)
    print(f"客户区矩形：{client_rect}")
    
    # 计算客户区中心点（按钮应该在这个位置）
    client_x = client_rect[2] // 2  # 客户区宽度的一半
    client_y = client_rect[3] // 2  # 客户区高度的一半
    
    print(f"\n客户区中心点：({client_x}, {client_y})")
    
    # 直接发送WM_LBUTTONDOWN和WM_L