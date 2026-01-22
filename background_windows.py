# -*- coding: utf-8 -*-
"""
自定义Windows设备类，实现基于SendInput的后台点击
不影响前台操作，支持真正的后台运行
支持虚拟屏幕和独立鼠标控制
"""

import time
import os
import win32gui
import win32con
import win32api
import pywintypes
import logging
import mss
import numpy
import ctypes
from ctypes import windll
from airtest.core.win.win import Windows
from virtual_display import virtual_display_manager
from independent_mouse import independent_mouse

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'background_windows.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('background_windows')

class BackgroundWindows(Windows):
    """
    自定义Windows设备类，使用SendInput实现后台点击
    不影响前台操作，支持真正的后台运行
    """
    
    def __init__(self, device):
        self.__dict__ = device.__dict__.copy()
        self.hwnd = None
        self.original_device = device
        self.is_embedded = False
        self.embedded_hwnd = None
        self.is_virtual_screen = False
        self.window_display = None
        self.independent_mouse = independent_mouse
        self.sendinput_restore_pos = True
    
    def init_hwnd(self, hwnd):
        self.hwnd = hwnd
        self.original_handle = getattr(self, 'handle', None)
        self.handle = hwnd
        
        try:
            parent_hwnd = win32gui.GetParent(hwnd)
            if parent_hwnd:
                self.is_embedded = True
                self.embedded_hwnd = hwnd
                logger.info(f"✓ 检测到嵌入窗口 (父窗口: {parent_hwnd})")
            else:
                self.is_embedded = False
                self.embedded_hwnd = None
                logger.info(f"✓ 窗口模式: 独立窗口")
        except pywintypes.error as e:
            logger.error(f"✗ 获取窗口信息失败: {e}")
            self.is_embedded = False
            self.embedded_hwnd = None
        
        try:
            virtual_display_manager.update_displays_info()
            self.window_display = virtual_display_manager.get_window_display(hwnd)
            if self.window_display and not self.window_display['is_primary']:
                self.is_virtual_screen = True
                logger.info(f"✓ 虚拟屏幕模式: 显示器 {self.window_display['id']}")
                self.independent_mouse.set_target_display(self.window_display)
            else:
                self.is_virtual_screen = False
                logger.info(f"✓ 主屏幕模式: 显示器 {self.window_display['id']}")
                self.independent_mouse.set_target_display(self.window_display)
        except Exception as e:
            logger.error(f"✗ 检测显示器失败: {e}")
            self.is_virtual_screen = False
            self.window_display = virtual_display_manager.get_main_display()
            self.independent_mouse.set_target_display(self.window_display)
    
    def _get_screen_coords(self, pos):
        if isinstance(pos, (list, tuple)):
            return pos
        elif hasattr(pos, 'match_result') and pos.match_result:
            return pos.match_result['result']
        elif isinstance(pos, dict):
            if 'x' in pos and 'y' in pos:
                return (pos['x'], pos['y'])
            elif 'result' in pos:
                return pos['result']
        try:
            return tuple(pos)
        except (TypeError, ValueError):
            return pos
    
    def snapshot(self, filename=None, quality=10, max_size=None, **kwargs):
        logger.info(f"📸 正在截图...")
        
        if not self.hwnd:
            logger.error("✗ 截图失败: 未设置窗口句柄")
            return None
        
        try:
            screen = self._snapshot_printwindow()
            
            if screen is None:
                logger.info("📸 尝试备用截图方法...")
                screen = self._snapshot_mss()
            
            if screen is None:
                logger.error("✗ 截图失败: 窗口可能已最小化或被系统保护")
                return None
                
            if filename:
                import aircv
                aircv.imwrite(filename, screen, quality, max_size=max_size)
                logger.info(f"💾 已保存截图: {filename}")
            
            logger.info(f"✓ 截图成功 (尺寸: {screen.shape[1]}x{screen.shape[0]})")
            return screen
            
        except Exception as e:
            logger.error(f"✗ 截图异常: {e}", exc_info=True)
            return None

    def _snapshot_printwindow(self):
        try:
            import win32ui
            import win32gui
            import win32con
            import cv2
            import numpy as np
            
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
                
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 2)
            if result == 0:
                result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 0)
            
            if result == 0:
                logger.error("✗ PrintWindow API 调用失败")
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwndDC)
                return None
                
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)
            
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)
            
            img = img[..., :3]
            img = img[..., ::-1]
            
            return img
            
        except Exception as e:
            logger.error(f"✗ PrintWindow 截图失败: {e}")
            return None

    def _snapshot_mss(self):
        try:
            rect = win32gui.GetWindowRect(self.hwnd)
            left, top, right, bottom = rect
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
                
            with mss.mss() as sct:
                monitor = {"top": top, "left": left, "width": width, "height": height}
                sct_img = sct.grab(monitor)
                screen = numpy.array(sct_img)
                if screen.shape[-1] >= 3:
                    screen = screen[..., :3]
                return screen
        except Exception as e:
            logger.error(f"✗ MSS 截图失败: {e}")
            return None
    
    def swipe(self, t1, t2, duration=0.5, steps=5, **kwargs):
        """
        后台滑动实现 (使用 SendInput)
        """
        if not self.hwnd:
            logger.error("✗ 滑动失败: 无窗口句柄")
            return False
            
        try:
            window_rect = win32gui.GetWindowRect(self.hwnd)
            window_left, window_top = window_rect[0], window_rect[1]
            
            x1, y1 = self._get_screen_coords(t1)
            x2, y2 = self._get_screen_coords(t2)
            
            screen_x1 = window_left + x1
            screen_y1 = window_top + y1
            screen_x2 = window_left + x2
            screen_y2 = window_top + y2
            
            logger.info(f"👆 滑动操作: 从 ({screen_x1}, {screen_y1}) 到 ({screen_x2}, {screen_y2})")
            logger.info(f"⏱️  滑动时长: {duration}秒, 分步数: {steps}")
            
            if steps < 1: steps = 1
            interval = duration / steps
            dx = (screen_x2 - screen_x1) / steps
            dy = (screen_y2 - screen_y1) / steps
            
            win32api.SetCursorPos((int(screen_x1), int(screen_y1)))
            
            self.independent_mouse.send_mouse_input(0, 0, win32con.MOUSEEVENTF_LEFTDOWN)
            
            for i in range(steps):
                cx = int(screen_x1 + dx * (i + 1))
                cy = int(screen_y1 + dy * (i + 1))
                win32api.SetCursorPos((cx, cy))
                time.sleep(interval)
                
            self.independent_mouse.send_mouse_input(0, 0, win32con.MOUSEEVENTF_LEFTUP)
            
            logger.info(f"✓ 滑动完成")
            return True
            
        except Exception as e:
            logger.error(f"✗ 滑动失败: {e}")
            return False

    def touch(self, pos, duration=0.1, right_click=False, steps=1, **kwargs):
        """
        后台点击实现 (使用 SendInput)
        """
        if not self.hwnd:
            logger.error("✗ 点击失败: 无窗口句柄")
            return False
        
        try:
            window_rect = win32gui.GetWindowRect(self.hwnd)
            window_left, window_top = window_rect[0], window_rect[1]
            
            if isinstance(pos, (list, tuple)):
                rel_x, rel_y = pos
                screen_x = window_left + rel_x
                screen_y = window_top + rel_y
            elif hasattr(pos, 'match_result'):
                rel_x, rel_y = pos.match_result['result']
                screen_x = window_left + rel_x
                screen_y = window_top + rel_y
            else:
                try:
                    rel_x, rel_y = tuple(pos)
                    screen_x = window_left + rel_x
                    screen_y = window_top + rel_y
                except:
                    screen_x, screen_y = 0, 0
            
            if pos == (-1, -1) or pos == [-1, -1]:
                width = window_rect[2] - window_rect[0]
                height = window_rect[3] - window_rect[1]
                screen_x = window_left + width // 2
                screen_y = window_top + height // 2
                logger.info(f"🎯 自动定位到窗口中心: ({screen_x}, {screen_y})")
            
            click_type = "右键" if right_click else "左键"
            logger.info(f"🖱️  {click_type}点击: 位置 ({screen_x}, {screen_y})")
            logger.info(f"⏱️  点击时长: {duration}秒")
            
            result = self.independent_mouse.perform_click(
                int(screen_x), 
                int(screen_y), 
                right_click, 
                self.sendinput_restore_pos,
                duration=duration
            )
            
            if result:
                logger.info(f"✓ 点击成功")
            else:
                logger.error(f"✗ 点击失败")
            
            return result
            
        except Exception as e:
            logger.error(f"✗ 点击异常: {e}", exc_info=True)
            return False
    
    def keyevent(self, keyname, **kwargs):
        """
        后台键盘事件实现
        Args:
            keyname: 按键名称
            **kwargs: 其他参数
        """
        if not self.hwnd:
            return super(BackgroundWindows, self).keyevent(keyname, **kwargs)
        
        key_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47,
            'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E,
            'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55,
            'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A, '0': 0x30, '1': 0x31,
            '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38,
            '9': 0x39, 'enter': 0x0D, 'return': 0x0D, 'backspace': 0x08, 'tab': 0x09,
            'space': 0x20, 'escape': 0x1B, 'left': 0x25, 'up': 0x26, 'right': 0x27,
            'down': 0x28,
        }
        
        key_code = key_map.get(keyname.lower(), None)
        if key_code:
            logger.info(f"⌨️  按键: {keyname}")
            win32api.keybd_event(key_code, 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(key_code, 0, 2, 0)
            return True
        else:
            logger.warning(f"⚠️  未知按键: {keyname}")
            return super(BackgroundWindows, self).keyevent(keyname, **kwargs)
    
    def type(self, text, with_spaces=False, **kwargs):
        """
        发送键盘消息实现后台输入
        Args:
            text: 要输入的文本
            with_spaces: 是否包含空格
            **kwargs: 其他参数
        """
        if not self.hwnd:
            return super(BackgroundWindows, self).type(text, with_spaces, **kwargs)
        
        try:
            logger.info(f"⌨️  输入文本: {text}")
            for char in text:
                win32api.keybd_event(ord(char), 0, 0, 0)
                time.sleep(0.01)
                win32api.keybd_event(ord(char), 0, 2, 0)
            logger.info(f"✓ 文本输入完成")
            return True
        except Exception as e:
            logger.error(f"✗ 文本输入失败: {e}", exc_info=True)
            return super(BackgroundWindows, self).type(text, with_spaces, **kwargs)
