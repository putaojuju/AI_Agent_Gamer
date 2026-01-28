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
import cv2
from mss import mss

class GameWindow:
    def __init__(self):
        self.hwnd = None # 主窗口句柄
        self.render_hwnd = None # 实际渲染的子窗口句柄
        self.window_title = ""
        self.width = 0
        self.height = 0

    def get_all_windows(self):
        """获取所有可见窗口"""
        windows = []
        def callback(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title != "Program Manager":
                    rect = win32gui.GetWindowRect(hwnd)
                    w = rect[2] - rect[0]
                    h = rect[3] - rect[1]
                    if w > 200 and h > 200: 
                        windows.append((hwnd, title))
            return True
        try:
            win32gui.EnumWindows(callback, None)
            windows.sort(key=lambda x: x[1])
            return windows
        except Exception as e:
            logging.error(f"枚举窗口失败: {e}")
            return []

    def init_hwnd(self, target_hwnd):
        """初始化句柄并寻找渲染子窗口"""
        try:
            target_hwnd = int(target_hwnd)
            if win32gui.IsWindow(target_hwnd):
                self.hwnd = target_hwnd
                self.window_title = win32gui.GetWindowText(target_hwnd)
                
                # --- 关键修改：寻找真正的渲染子窗口 ---
                self.render_hwnd = self._find_render_child(self.hwnd)
                
                # 如果没找到子窗口，回退到主窗口
                final_hwnd = self.render_hwnd if self.render_hwnd else self.hwnd
                
                # 获取尺寸
                rect = win32gui.GetClientRect(final_hwnd)
                self.width = rect[2] - rect[0]
                self.height = rect[3] - rect[1]
                
                logging.info(f"窗口锁定: {self.window_title} (Main: {self.hwnd}, Render: {self.render_hwnd})")
                return True
            else:
                return False
        except Exception as e:
            logging.error(f"初始化失败: {e}")
            return False

    def _find_render_child(self, parent_hwnd):
        """
        遍历寻找面积最大的子窗口
        Unity/DMM 游戏通常在子窗口中渲染
        """
        child_windows = []
        def callback(hwnd, extra):
            # 必须是可见的子窗口
            if win32gui.IsWindowVisible(hwnd):
                rect = win32gui.GetClientRect(hwnd)
                area = (rect[2] - rect[0]) * (rect[3] - rect[1])
                child_windows.append((hwnd, area))
            return True
        
        try:
            win32gui.EnumChildWindows(parent_hwnd, callback, None)
            if not child_windows:
                return None
            
            # 按面积降序排列，取最大的那个
            child_windows.sort(key=lambda x: x[1], reverse=True)
            best_child = child_windows[0][0]
            
            # 如果最大的子窗口面积太小（比如只是个按钮），则认为没有渲染窗口
            if child_windows[0][1] < 10000:
                return None
                
            return best_child
        except Exception:
            return None

    def snapshot(self):
        """
        截图方法：优先对渲染子窗口使用 PrintWindow
        如果检测到黑屏/白屏，自动切换到 MSS 屏幕截图
        """
        # 优先使用子窗口，没有则用主窗口
        target_hwnd = self.render_hwnd if self.render_hwnd else self.hwnd
        
        if not target_hwnd: return None

        try:
            img = self._capture_with_printwindow(target_hwnd)
            
            # 检测是否为纯色图片（黑屏/白屏）
            if img is not None and self._is_solid_color(img):
                logging.warning("检测到黑屏/白屏，切换到 MSS 屏幕截图模式")
                img = self._capture_with_mss(target_hwnd)
            
            return img
            
        except Exception as e:
            logging.error(f"截图失败: {e}")
            return None
    
    def _capture_with_printwindow(self, target_hwnd):
        """使用 PrintWindow API 截取窗口"""
        try:
            left, top, right, bottom = win32gui.GetClientRect(target_hwnd)
            w = right - left
            h = bottom - top
            
            if w <= 0 or h <= 0: return None

            hwindc = win32gui.GetWindowDC(target_hwnd)
            srcdc = win32ui.CreateDCFromHandle(hwindc)
            memdc = srcdc.CreateCompatibleDC()
            
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(srcdc, w, h)
            memdc.SelectObject(bmp)
            
            # 使用 PrintWindow (Flag 2) 截取后台画面
            result = ctypes.windll.user32.PrintWindow(target_hwnd, memdc.GetSafeHdc(), 2)
            
            # 如果失败，尝试旧版 Flag 0
            if result == 0:
                ctypes.windll.user32.PrintWindow(target_hwnd, memdc.GetSafeHdc(), 0)
            
            bmp_str = bmp.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype='uint8')
            img.shape = (h, w, 4)
            
            win32gui.DeleteObject(bmp.GetHandle())
            memdc.DeleteDC()
            srcdc.DeleteDC()
            win32gui.ReleaseDC(target_hwnd, hwindc)

            return img[:, :, :3][..., ::-1]
            
        except Exception as e:
            logging.error(f"PrintWindow 截图失败: {e}")
            return None
    
    def _capture_with_mss(self, target_hwnd):
        """使用 MSS 库截取屏幕指定区域（要求窗口在前台）"""
        try:
            # 获取窗口在屏幕上的位置
            rect = win32gui.GetWindowRect(target_hwnd)
            left, top, right, bottom = rect
            w = right - left
            h = bottom - top
            
            if w <= 0 or h <= 0: return None
            
            with mss() as sct:
                monitor = {"left": left, "top": top, "width": w, "height": h}
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                # MSS 返回的是 BGRA，转换为 BGR
                if img.shape[-1] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                return img
                
        except Exception as e:
            logging.error(f"MSS 截图失败: {e}")
            return None
    
    def _is_solid_color(self, img: np.ndarray, threshold: float = 10.0) -> bool:
        """检测图片是否为纯色（方差极低）
        
        Args:
            img: numpy 图像数组 (BGR 格式)
            threshold: 方差阈值，低于此值认为是纯色（默认 10.0）
        
        Returns:
            是否为纯色图片
        """
        if img is None or img.size == 0:
            return True
        
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # 计算方差
            variance = np.var(gray)
            return variance < threshold
        except Exception:
            return False