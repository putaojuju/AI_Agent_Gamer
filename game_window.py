# -*- coding: utf-8 -*-
"""
游戏窗口管理
仅依赖 win32gui 和 mss，实现窗口句柄初始化和截图功能
"""

import win32gui
import mss
from PIL import Image

class GameWindow:
    def __init__(self):
        self.hwnd = None
        self.sct = mss.mss()
    
    def init_hwnd(self, hwnd):
        """
        初始化窗口句柄
        :param hwnd: 窗口句柄
        """
        self.hwnd = hwnd
    
    def get_rect(self):
        """
        获取窗口客户区的屏幕坐标
        :return: (left, top, right, bottom) 屏幕坐标
        """
        if not self.hwnd:
            return None
        
        try:
            # 获取窗口客户区坐标（相对于窗口）
            client_rect = win32gui.GetClientRect(self.hwnd)
            
            # 转换为屏幕坐标
            left, top = win32gui.ClientToScreen(self.hwnd, (client_rect[0], client_rect[1]))
            right, bottom = win32gui.ClientToScreen(self.hwnd, (client_rect[2], client_rect[3]))
            
            return (left, top, right, bottom)
        except Exception:
            return None
    
    def snapshot(self):
        """
        基于客户区进行 MSS 截图
        :return: PIL.Image 对象
        """
        rect = self.get_rect()
        if not rect:
            return None
        
        try:
            # 构建 MSS 截图区域
            monitor = {
                "top": rect[1],
                "left": rect[0],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }
            
            # 截图
            sct_img = self.sct.grab(monitor)
            
            # 转换为 PIL Image
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            
            return img
        except Exception:
            return None
    
    def is_valid(self):
        """
        检查窗口是否有效
        :return: bool
        """
        if not self.hwnd:
            return False
        
        try:
            # 检查窗口是否存在
            return win32gui.IsWindow(self.hwnd)
        except Exception:
            return False
    
    def get_window_title(self):
        """
        获取窗口标题
        :return: str
        """
        if not self.hwnd:
            return ""
        
        try:
            return win32gui.GetWindowText(self.hwnd)
        except Exception:
            return ""

# 单例模式
game_window = GameWindow()
