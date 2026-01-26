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
        混合截图策略：
        1. 针对 Unity/DirectX：使用屏幕截取 (BitBlt from Screen DC)。
        2. 坐标修正：使用 ClientToScreen 确保只截取游戏画面，不含标题栏。
        """
        if not self.hwnd: return None

        try:
            # 1. 获取客户区大小 (去掉标题栏的纯画面区域)
            left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
            w = right - left
            h = bottom - top
            
            if w <= 0 or h <= 0: return None

            # 2. 将客户区左上角 (0,0) 转换为屏幕绝对坐标
            # 这解决了 DPI 缩放导致的错位问题，也确定了在屏幕上的真实位置
            client_point = win32gui.ClientToScreen(self.hwnd, (0, 0))
            screen_x, screen_y = client_point

            # 3. 准备截图资源
            # 获取整个屏幕的 DC (HWND_DESKTOP = 0)
            # 这种方式对 Unity 兼容性最好，因为它截取的是显卡最终输出的画面
            hwindc = win32gui.GetDC(0) 
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, w, h)
            memdc.SelectObject(bmp)
            
            # 4. 执行截图：从屏幕 DC 复制指定区域到内存 DC
            # 参数: (目标x, 目标y), (宽, 高), 源DC, (源x, 源y), 操作码
            memdc.BitBlt((0, 0), (w, h), srcdc, (screen_x, screen_y), win32con.SRCCOPY)
            
            # 5. 提取数据
            bmp_str = bmp.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype='uint8')
            img.shape = (h, w, 4)
            
            # 6. 清理资源 (非常重要，否则会内存泄漏)
            win32gui.DeleteObject(bmp.GetHandle())
            memdc.DeleteDC()
            srcdc.DeleteDC()
            win32gui.ReleaseDC(0, hwindc) # 释放屏幕 DC

            # 7. 格式转换 BGRA -> RGB
            return img[:, :, :3][..., ::-1]
            
        except Exception as e:
            # 可以在这里记录日志
            logging.error(f"Snapshot Error: {e}")
            return None