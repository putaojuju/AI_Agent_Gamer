import win32gui
import win32api
import win32con
import mss
import numpy as np
from typing import Optional, Tuple

class GameWindow:
    def __init__(self):
        self.hwnd: Optional[int] = None
        self.sct = mss.mss()
    
    def init_hwnd(self, window_title: str) -> bool:
        """初始化窗口句柄"""
        def callback(hwnd, titles):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    titles.append((hwnd, title))
            return True
        
        titles = []
        win32gui.EnumWindows(callback, titles)
        
        for hwnd, title in titles:
            if window_title in title:
                self.hwnd = hwnd
                return True
        
        return False
    
    def get_rect(self) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口客户区的屏幕绝对坐标"""
        if not self.hwnd:
            return None
        
        # 获取客户区坐标（相对于窗口左上角）
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        
        # 将客户区坐标转换为屏幕绝对坐标
        left, top = win32gui.ClientToScreen(self.hwnd, (left, top))
        right, bottom = win32gui.ClientToScreen(self.hwnd, (right, bottom))
        
        return left, top, right, bottom
    
    def snapshot(self) -> Optional[np.ndarray]:
        """获取窗口截图"""
        rect = self.get_rect()
        if not rect:
            return None
        
        left, top, right, bottom = rect
        monitor = {
            "top": top,
            "left": left,
            "width": right - left,
            "height": bottom - top
        }
        
        try:
            img = self.sct.grab(monitor)
            img_array = np.array(img)
            # 转换为RGB格式（去掉alpha通道）
            if img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            return img_array
        except Exception:
            return None
    
    def is_active(self) -> bool:
        """检查窗口是否激活"""
        if not self.hwnd:
            return False
        return win32gui.GetForegroundWindow() == self.hwnd
    
    def set_foreground(self) -> bool:
        """设置窗口为前台"""
        if not self.hwnd:
            return False
        
        try:
            # 先最小化再还原，确保窗口能正确显示
            win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(self.hwnd)
            return True
        except Exception:
            return False
