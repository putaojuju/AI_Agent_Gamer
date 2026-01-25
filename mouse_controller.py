import win32api
import win32con
import ctypes
from typing import Optional

class MouseController:
    def __init__(self):
        pass
    
    def click(self, window_x: int, window_y: int, hwnd: Optional[int] = None) -> bool:
        """点击指定位置
        
        Args:
            window_x: 窗口内的X坐标
            window_y: 窗口内的Y坐标
            hwnd: 窗口句柄（用于坐标转换）
            
        Returns:
            是否点击成功
        """
        try:
            if hwnd:
                # 获取窗口左上角坐标
                left, top, _, _ = win32api.GetWindowRect(hwnd)
                # 转换为屏幕坐标
                screen_x = left + window_x
                screen_y = top + window_y
            else:
                # 如果没有提供句柄，直接使用传入的坐标
                screen_x = window_x
                screen_y = window_y
            
            # 移动鼠标到目标位置
            win32api.SetCursorPos((screen_x, screen_y))
            
            # 模拟左键点击
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            return True
        except Exception:
            return False
    
    def double_click(self, window_x: int, window_y: int, hwnd: Optional[int] = None) -> bool:
        """双击指定位置"""
        try:
            if hwnd:
                left, top, _, _ = win32api.GetWindowRect(hwnd)
                screen_x = left + window_x
                screen_y = top + window_y
            else:
                screen_x = window_x
                screen_y = window_y
            
            win32api.SetCursorPos((screen_x, screen_y))
            
            # 模拟双击
            for _ in range(2):
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            return True
        except Exception:
            return False
    
    def right_click(self, window_x: int, window_y: int, hwnd: Optional[int] = None) -> bool:
        """右键点击指定位置"""
        try:
            if hwnd:
                left, top, _, _ = win32api.GetWindowRect(hwnd)
                screen_x = left + window_x
                screen_y = top + window_y
            else:
                screen_x = window_x
                screen_y = window_y
            
            win32api.SetCursorPos((screen_x, screen_y))
            
            # 模拟右键点击
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            
            return True
        except Exception:
            return False
    
    def move(self, window_x: int, window_y: int, hwnd: Optional[int] = None) -> bool:
        """移动鼠标到指定位置"""
        try:
            if hwnd:
                left, top, _, _ = win32api.GetWindowRect(hwnd)
                screen_x = left + window_x
                screen_y = top + window_y
            else:
                screen_x = window_x
                screen_y = window_y
            
            win32api.SetCursorPos((screen_x, screen_y))
            return True
        except Exception:
            return False
