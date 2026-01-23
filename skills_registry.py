# -*- coding: utf-8 -*-
"""
技能注册表模块
使用 LangChain 的 tool 装饰器封装原子操作供 Agent 调用
"""

import win32gui
import win32api
import win32con
import time
from typing import Optional, Tuple
from langchain_core.tools import tool
import logging

log_dir = "log"
import os
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'skills_registry.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('skills_registry')


class SkillsRegistry:
    """
    技能注册表类，管理所有可用的操作工具
    """
    
    def __init__(self, hwnd: Optional[int] = None):
        """
        初始化技能注册表
        
        Args:
            hwnd: 目标窗口句柄
        """
        self.hwnd = hwnd
        self.vision = None
        logger.info(f"技能注册表初始化完成，窗口句柄: {hwnd}")
    
    def set_vision(self, vision):
        """
        设置视觉核心实例
        
        Args:
            vision: VisionCore 实例
        """
        self.vision = vision
    
    def _get_window_coords(self) -> Tuple[int, int]:
        """
        获取窗口左上角坐标
        
        Returns:
            (window_left, window_top)
        """
        if self.hwnd:
            rect = win32gui.GetWindowRect(self.hwnd)
            return rect[0], rect[1]
        return 0, 0
    
    def _perform_click(self, x: int, y: int, right_click: bool = False) -> bool:
        """
        执行点击操作
        
        Args:
            x: 相对 X 坐标
            y: 相对 Y 坐标
            right_click: 是否右键点击
        
        Returns:
            是否成功
        """
        try:
            window_left, window_top = self._get_window_coords()
            screen_x = window_left + x
            screen_y = window_top + y
            
            click_type = "右键" if right_click else "左键"
            logger.info(f"{click_type}点击: 相对坐标({x}, {y}), 屏幕坐标({screen_x}, {screen_y})")
            
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.05)
            
            if right_click:
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            else:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.05)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            logger.info("点击成功")
            return True
            
        except Exception as e:
            logger.error(f"点击失败: {e}")
            return False


def click_text(text: str, confidence_threshold: float = 0.5) -> str:
    """
    使用 OCR 查找并点击指定文字
    
    Args:
        text: 要点击的文字内容
        confidence_threshold: OCR 置信度阈值，默认 0.5
    
    Returns:
        操作结果描述
    """
    try:
        from vision_core import VisionCore
        
        vision = VisionCore()
        result = vision.find_text(text, confidence_threshold)
        
        if result:
            x, y, confidence = result
            logger.info(f"找到文字 '{text}'，坐标: ({x}, {y})，置信度: {confidence:.2f}")
            
            win32api.SetCursorPos((x, y))
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            
            return f"成功点击文字 '{text}'，坐标: ({x}, {y})"
        else:
            return f"未找到文字 '{text}'"
            
    except Exception as e:
        logger.error(f"点击文字失败: {e}")
        return f"点击文字失败: {str(e)}"


def click_grid_coordinate(row: int, col: int, grid_size: int = 4) -> str:
    """
    点击指定网格坐标
    
    Args:
        row: 行索引 (0 到 grid_size-1)
        col: 列索引 (0 到 grid_size-1)
        grid_size: 网格大小，默认 4x4
    
    Returns:
        操作结果描述
    """
    try:
        if row < 0 or row >= grid_size or col < 0 or col >= grid_size:
            return f"网格坐标超出范围: ({row}, {col})，有效范围: 0-{grid_size-1}"
        
        from vision_core import VisionCore
        
        vision = VisionCore()
        screenshot_array = vision.capture()
        
        if screenshot_array is None:
            return "截图失败"
        
        height, width = screenshot_array.shape[:2]
        cell_width = width / grid_size
        cell_height = height / grid_size
        
        x = int((col + 0.5) * cell_width)
        y = int((row + 0.5) * cell_height)
        
        logger.info(f"点击网格坐标: 行{row}, 列{col}，像素坐标: ({x}, {y})")
        
        win32api.SetCursorPos((x, y))
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.05)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        return f"成功点击网格坐标: 行{row}, 列{col}，像素坐标: ({x}, {y})"
        
    except Exception as e:
        logger.error(f"点击网格坐标失败: {e}")
        return f"点击网格坐标失败: {str(e)}"


def key_press(key_name: str, duration: float = 0.1) -> str:
    """
    按下并释放指定按键
    
    Args:
        key_name: 按键名称，如 'a', 'enter', 'space', 'esc'
        duration: 按键持续时间（秒），默认 0.1
    
    Returns:
        操作结果描述
    """
    try:
        key_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47,
            'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E,
            'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55,
            'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A, '0': 0x30, '1': 0x31,
            '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38,
            '9': 0x39, 'enter': 0x0D, 'return': 0x0D, 'backspace': 0x08, 'tab': 0x09,
            'space': 0x20, 'escape': 0x1B, 'esc': 0x1B, 'left': 0x25, 'up': 0x26,
            'right': 0x27, 'down': 0x28, 'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
            'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
            'f11': 0x7A, 'f12': 0x7B,
        }
        
        key_code = key_map.get(key_name.lower())
        if key_code is None:
            return f"未知按键: {key_name}"
        
        logger.info(f"按下按键: {key_name}")
        win32api.keybd_event(key_code, 0, 0, 0)
        time.sleep(duration)
        win32api.keybd_event(key_code, 0, 2, 0)
        
        return f"成功按下按键: {key_name}"
        
    except Exception as e:
        logger.error(f"按键失败: {e}")
        return f"按键失败: {str(e)}"


def wait(seconds: float) -> str:
    """
    等待指定时间
    
    Args:
        seconds: 等待时间（秒）
    
    Returns:
        操作结果描述
    """
    try:
        logger.info(f"等待 {seconds} 秒")
        time.sleep(seconds)
        return f"已等待 {seconds} 秒"
    except Exception as e:
        logger.error(f"等待失败: {e}")
        return f"等待失败: {str(e)}"


def get_all_tools():
    """
    获取所有可用的工具列表
    
    Returns:
        LangChain 工具列表
    """
    return [click_text, click_grid_coordinate, key_press, wait]


if __name__ == "__main__":
    print("技能注册表模块测试")
    print("使用示例:")
    print("""
    from skills_registry import get_all_tools
    
    # 获取所有工具
    tools = get_all_tools()
    for tool in tools:
        print(f"工具: {tool.name}, 描述: {tool.description}")
    """)
