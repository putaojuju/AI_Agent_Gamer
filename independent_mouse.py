# -*- coding: utf-8 -*-
"""
独立鼠标控制模块
实现虚拟屏幕的鼠标操作,使用 SendInput (Mouse Teleport) 方式
"""

import os
import time
import win32gui
import win32con
import win32api
import ctypes
import logging
from ctypes import wintypes
from virtual_display import virtual_display_manager

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'independent_mouse.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('independent_mouse')

huser32 = ctypes.WinDLL('user32', use_last_error=True)

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_void_p),
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
        ]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]

INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_XDOWN = 0x0100
MOUSEEVENTF_XUP = 0x0200

class IndependentMouse:
    """
    独立鼠标控制器
    使用 SendInput 实现虚拟屏幕鼠标操作
    """
    
    def __init__(self):
        self.target_display = None
        virtual_display_manager.update_displays_info()
        self.main_display = virtual_display_manager.get_main_display()
        self.virtual_display = virtual_display_manager.get_virtual_display()
        logger.info("✓ 独立鼠标控制器已初始化")
    
    def set_target_display(self, display):
        if isinstance(display, dict):
            self.target_display = display
        elif isinstance(display, int):
            displays = virtual_display_manager.get_displays()
            for d in displays:
                if d['id'] == display:
                    self.target_display = d
                    break
        
        if self.target_display:
            logger.info(f"✓ 目标显示器已设置为: {self.target_display['id']}")
        else:
            logger.warning("⚠️  未找到指定的目标显示器")
    
    def set_target_display_to_virtual(self):
        self.target_display = self.virtual_display
        if self.virtual_display:
            logger.info(f"✓ 目标显示器已设置为虚拟屏幕: {self.virtual_display['id']}")
    
    def set_target_display_to_main(self):
        self.target_display = self.main_display
        logger.info(f"✓ 目标显示器已设置为主屏幕: {self.main_display['id']}")
    
    def send_mouse_input(self, dx, dy, dwFlags, mouseData=0):
        try:
            if not self.target_display:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    self.target_display = virtual_display_manager.get_window_display(hwnd)
                else:
                    self.target_display = self.main_display
            
            mi = MOUSEINPUT()
            
            if dwFlags & MOUSEEVENTF_ABSOLUTE:
                screen_width = self.target_display['width']
                screen_height = self.target_display['height']
                screen_left = self.target_display['left']
                screen_top = self.target_display['top']
                
                target_x = dx - screen_left
                target_y = dy - screen_top
                
                target_x = max(0, min(target_x, screen_width))
                target_y = max(0, min(target_y, screen_height))
                
                mi.dx = int((target_x / screen_width) * 65535)
                mi.dy = int((target_y / screen_height) * 65535)
                
                logger.debug(f"📍 坐标转换: ({dx}, {dy}) -> ({target_x}, {target_y}) -> ({mi.dx}, {mi.dy})")
            else:
                mi.dx = dx
                mi.dy = dy
            
            mi.mouseData = mouseData
            mi.dwFlags = dwFlags
            mi.time = 0
            mi.dwExtraInfo = huser32.GetMessageExtraInfo()
            
            inp = INPUT()
            inp.type = INPUT_MOUSE
            inp.mi = mi
            
            nInputs = 1
            cbSize = ctypes.sizeof(INPUT)
            
            result = huser32.SendInput(nInputs, ctypes.byref(inp), cbSize)
            
            if result != nInputs:
                raise ctypes.WinError(ctypes.get_last_error())
            
            logger.debug(f"🖱️  鼠标输入已发送")
            return True
        except Exception as e:
            logger.error(f"✗ 发送鼠标输入失败: {e}")
            return False
    
    def update_display_info(self):
        virtual_display_manager.update_displays_info()
        self.main_display = virtual_display_manager.get_main_display()
        self.virtual_display = virtual_display_manager.get_virtual_display()
        logger.info("✓ 显示器信息已更新")
    
    def perform_click(self, x, y, right_click=False, restore_pos=True, duration=0.05):
        """
        SendInput 瞬移点击实现
        Args:
            x: 虚拟屏幕上的绝对坐标
            y: 虚拟屏幕上的绝对坐标
            right_click: 是否右键点击
            restore_pos: 是否恢复鼠标位置 (默认True，设为False可观察鼠标移动)
            duration: 点击持续时间 (秒)
        Returns:
            bool: 是否点击成功
        """
        original_pos = None
        try:
            click_type = "右键" if right_click else "左键"
            logger.info(f"🖱️  {click_type}点击: 位置 ({x}, {y}), 时长 {duration}秒")
            
            if restore_pos:
                original_pos = win32api.GetCursorPos()
                logger.debug(f"💾 保存原始鼠标位置: {original_pos}")
            
            win32api.SetCursorPos((x, y))
            logger.debug(f"📍 鼠标已移动到目标位置")
            
            button_down = win32con.MOUSEEVENTF_RIGHTDOWN if right_click else win32con.MOUSEEVENTF_LEFTDOWN
            button_up = win32con.MOUSEEVENTF_RIGHTUP if right_click else win32con.MOUSEEVENTF_LEFTUP
            
            self.send_mouse_input(0, 0, button_down)
            logger.debug(f"🖱️  按下{click_type}")
            
            time.sleep(duration)
            logger.debug(f"⏱️  保持点击 {duration}秒")
            
            logger.info(f"✓ {click_type}点击成功")
            return True
        except Exception as e:
            logger.error(f"✗ 点击失败: {e}")
            return False
        finally:
            try:
                button_up = win32con.MOUSEEVENTF_RIGHTUP if right_click else win32con.MOUSEEVENTF_LEFTUP
                self.send_mouse_input(0, 0, button_up)
                logger.debug(f"🖱️  释放{click_type}")
            except Exception as e:
                logger.error(f"✗ 释放鼠标失败: {e}")

            if restore_pos and original_pos:
                try:
                    win32api.SetCursorPos(original_pos)
                    logger.debug(f"📍 恢复原始鼠标位置")
                except:
                    pass

independent_mouse = IndependentMouse()

if __name__ == "__main__":
    im = IndependentMouse()
    im.update_display_info()
    im.set_target_display_to_virtual()
    
    if im.virtual_display:
        center_x = im.virtual_display['width'] // 2
        center_y = im.virtual_display['height'] // 2
        print(f"在虚拟屏幕中心 ({center_x}, {center_y}) 点击")
        im.perform_click(center_x, center_y)
    else:
        print("未检测到虚拟屏幕，无法进行测试")
