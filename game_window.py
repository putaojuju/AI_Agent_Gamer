# -*- coding: utf-8 -*-
# DPI 感知设置
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

import win32gui
import win32ui
import win32con
import numpy as np
import logging

class GameWindow:
    def __init__(self):
        self.hwnd = None
        self.window_title = ""
        self.width = 0
        self.height = 0

    def get_all_windows(self):
        """
        获取当前所有可见窗口的列表
        返回: List[Tuple(hwnd, title)]
        """
        windows = []
        
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # 过滤逻辑：
                # 1. 标题不为空
                # 2. 忽略 "Program Manager" 等系统窗口
                if title and title != "Program Manager":
                    # 3. 尺寸过滤：太小的窗口通常不是游戏 (例如小于 200x200)
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2] - rect[0]
                    h = rect[3] - rect[1]
                    if w > 200 and h > 200: 
                        windows.append((hwnd, title))
            return True

        try:
            win32gui.EnumWindows(callback, None)
            # 按标题排序，方便查找
            windows.sort(key=lambda x: x[1])
            return windows
        except Exception as e:
            logging.error(f"枚举窗口失败: {e}")
            return []

    def init_hwnd(self, target_hwnd):
        """
        直接通过句柄初始化
        Args:
            target_hwnd: 窗口句柄 ID (int)
        """
        try:
            # 确保句柄是整数
            target_hwnd = int(target_hwnd)
            
            if win32gui.IsWindow(target_hwnd):
                self.hwnd = target_hwnd
                self.window_title = win32gui.GetWindowText(target_hwnd)
                
                # 获取窗口大小
                rect = win32gui.GetWindowRect(target_hwnd)
                self.width = rect[2] - rect[0]
                self.height = rect[3] - rect[1]
                
                logging.info(f"窗口已锁定: {self.window_title} (HWND: {self.hwnd})")
                return True
            else:
                logging.warning(f"无效的窗口句柄: {target_hwnd}")
                return False
        except Exception as e:
            logging.error(f"初始化窗口句柄失败: {e}")
            return False

    def snapshot(self):
        """
        后台截图 (PrintWindow)
        """
        if not self.hwnd:
            return None

        try:
            # 获取客户区尺寸（去掉标题栏）
            left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
            w = right - left
            h = bottom - top
            
            if w <= 0 or h <= 0: return None

            # 创建设备上下文
            hwindc = win32gui.GetWindowDC(self.hwnd)
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            
            # 创建位图
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, w, h)
            memdc.SelectObject(bmp)
            
            # 截图核心：
            # 参数 0: PrintWindow (包含标题栏，兼容性最好)
            # 参数 1: (某些系统版本不同)
            # 参数 2: PrintClient (仅内容区，容易黑屏)
            # 这里的 0 通常对模拟器兼容性最好
            result = ctypes.windll.user32.PrintWindow(self.hwnd, memdc.GetSafeHdc(), 0) 
            
            bmp_info = bmp.GetInfo()
            bmp_str = bmp.GetBitmapBits(True)
            
            # 转为 numpy 数组
            img = np.frombuffer(bmp_str, dtype='uint8')
            img.shape = (h, w, 4)
            
            # 清理资源
            win32gui.DeleteObject(bmp.GetHandle())
            memdc.DeleteDC()
            srcdc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwindc)

            # 去掉 Alpha 通道，转为 RGB (兼容 PIL/OpenCV)
            # 这里的切片操作：[保留所有行, 保留所有列, 取前3个通道(BGR)][RGB反转]
            return img[:, :, :3][..., ::-1]
            
        except Exception as e:
            logging.error(f"截图失败: {e}")
            return None