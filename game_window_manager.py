# -*- coding: utf-8 -*-
"""
游戏窗口管理模块
实现游戏窗口的自动检测、定位和管理功能
"""

import win32gui
import win32con
import logging
import time
from virtual_display import virtual_display_manager

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_window_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('game_window_manager')

class GameWindowManager:
    """
    游戏窗口管理器
    负责游戏窗口的检测、定位和管理
    """
    
    def __init__(self):
        """
        初始化游戏窗口管理器
        """
        self.game_windows = {}
        self.update_game_windows()
    
    def update_game_windows(self):
        """
        更新游戏窗口列表
        """
        self.game_windows = {}
        
        def enum_windows_proc(hwnd, lparam):
            if win32gui.IsWindowVisible(hwnd):
                # 获取窗口标题
                window_title = win32gui.GetWindowText(hwnd)
                if window_title:
                    # 获取窗口类名
                    class_name = win32gui.GetClassName(hwnd)
                    # 获取窗口位置和大小
                    rect = win32gui.GetWindowRect(hwnd)
                    width = rect[2] - rect[0]
                    height = rect[3] - rect[1]
                    
                    # 只添加有实际内容的窗口（排除空窗口和任务栏等）
                    if width > 100 and height > 100:
                        self.game_windows[hwnd] = {
                            'title': window_title,
                            'class_name': class_name,
                            'left': rect[0],
                            'top': rect[1],
                            'width': width,
                            'height': height
                        }
            return True
        
        # 枚举所有可见窗口
        win32gui.EnumWindows(enum_windows_proc, None)
        logger.info(f"检测到 {len(self.game_windows)} 个可见窗口")
    
    def find_game_window(self, title_pattern, class_pattern=None):
        """
        根据标题和类名查找游戏窗口
        Args:
            title_pattern: 窗口标题模式（支持模糊匹配）
            class_pattern: 窗口类名模式（可选，支持模糊匹配）
        Returns:
            int: 窗口句柄，如果没有找到则返回0
        """
        # 更新窗口列表
        self.update_game_windows()
        
        matching_windows = []
        for hwnd, window_info in self.game_windows.items():
            # 检查标题匹配
            title_match = title_pattern.lower() in window_info['title'].lower()
            # 检查类名匹配（如果提供了类名模式）
            class_match = class_pattern is None or class_pattern.lower() in window_info['class_name'].lower()
            
            if title_match and class_match:
                matching_windows.append(hwnd)
        
        if matching_windows:
            logger.info(f"找到 {len(matching_windows)} 个匹配的窗口")
            # 返回第一个匹配的窗口
            return matching_windows[0]
        else:
            logger.warning(f"未找到匹配的窗口：标题包含 '{title_pattern}'")
            return 0
    
    def get_window_info(self, hwnd):
        """
        获取窗口信息
        Args:
            hwnd: 窗口句柄
        Returns:
            dict: 窗口信息，如果窗口不存在则返回None
        """
        if hwnd in self.game_windows:
            return self.game_windows[hwnd]
        
        # 如果窗口不在缓存中，尝试直接获取
        try:
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                width = rect[2] - rect[0]
                height = rect[3] - rect[1]
                
                window_info = {
                    'title': window_title,
                    'class_name': class_name,
                    'left': rect[0],
                    'top': rect[1],
                    'width': width,
                    'height': height
                }
                self.game_windows[hwnd] = window_info
                return window_info
        except Exception as e:
            logger.error(f"获取窗口 {hwnd} 信息失败: {e}")
        
        return None
    
    def move_game_to_virtual_screen(self, hwnd_or_title):
        """
        将游戏窗口移动到虚拟屏幕
        Args:
            hwnd_or_title: 窗口句柄或窗口标题
        Returns:
            bool: 是否移动成功
        """
        # 如果是字符串，查找窗口句柄
        if isinstance(hwnd_or_title, str):
            hwnd = self.find_game_window(hwnd_or_title)
            if not hwnd:
                return False
        else:
            hwnd = hwnd_or_title
        
        # 确保虚拟屏幕存在
        virtual_display_manager.update_displays_info()
        virtual_display = virtual_display_manager.get_virtual_display()
        if not virtual_display:
            logger.error("未检测到虚拟屏幕")
            return False
        
        # 移动窗口到虚拟屏幕
        success = virtual_display_manager.move_window_to_virtual_display(hwnd)
        if success:
            # 激活窗口
            virtual_display_manager.activate_window(hwnd)
            logger.info(f"游戏窗口 {hwnd} 已成功移动到虚拟屏幕")
            return True
        else:
            logger.error(f"移动游戏窗口 {hwnd} 到虚拟屏幕失败")
            return False
    
    def move_game_to_main_screen(self, hwnd_or_title):
        """
        将游戏窗口移动到主屏幕
        Args:
            hwnd_or_title: 窗口句柄或窗口标题
        Returns:
            bool: 是否移动成功
        """
        # 如果是字符串，查找窗口句柄
        if isinstance(hwnd_or_title, str):
            hwnd = self.find_game_window(hwnd_or_title)
            if not hwnd:
                return False
        else:
            hwnd = hwnd_or_title
        
        # 确保主屏幕存在
        virtual_display_manager.update_displays_info()
        main_display = virtual_display_manager.get_main_display()
        if not main_display:
            logger.error("未检测到主屏幕")
            return False
        
        # 移动窗口到主屏幕
        success = virtual_display_manager.move_window_to_display(hwnd, main_display)
        if success:
            # 激活窗口
            virtual_display_manager.activate_window(hwnd)
            logger.info(f"游戏窗口 {hwnd} 已成功移动到主屏幕")
            return True
        else:
            logger.error(f"移动游戏窗口 {hwnd} 到主屏幕失败")
            return False
    
    def get_window_display(self, hwnd):
        """
        获取窗口所在的显示器
        Args:
            hwnd: 窗口句柄
        Returns:
            dict: 显示器信息
        """
        virtual_display_manager.update_displays_info()
        return virtual_display_manager.get_window_display(hwnd)
    
    def is_window_on_virtual_screen(self, hwnd):
        """
        检查窗口是否在虚拟屏幕上
        Args:
            hwnd: 窗口句柄
        Returns:
            bool: 是否在虚拟屏幕上
        """
        display = self.get_window_display(hwnd)
        return display is not None and not display['is_primary']
    
    def maximize_window(self, hwnd):
        """
        最大化窗口
        Args:
            hwnd: 窗口句柄
        Returns:
            bool: 是否最大化成功
        """
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            logger.info(f"窗口 {hwnd} 已最大化")
            return True
        except Exception as e:
            logger.error(f"最大化窗口 {hwnd} 失败: {e}")
            return False
    
    def close_window(self, hwnd):
        """
        关闭窗口
        Args:
            hwnd: 窗口句柄
        Returns:
            bool: 是否关闭成功
        """
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            logger.info(f"已发送关闭消息到窗口 {hwnd}")
            return True
        except Exception as e:
            logger.error(f"关闭窗口 {hwnd} 失败: {e}")
            return False

# 单例模式
game_window_manager = GameWindowManager()

# 测试代码
if __name__ == "__main__":
    gwm = GameWindowManager()
    
    # 查找记事本窗口（示例）
    notepad_hwnd = gwm.find_game_window("记事本")
    if notepad_hwnd:
        print(f"找到记事本窗口：{notepad_hwnd}")
        window_info = gwm.get_window_info(notepad_hwnd)
        print(f"窗口信息：{window_info}")
        
        # 检查是否在虚拟屏幕上
        is_on_virtual = gwm.is_window_on_virtual_screen(notepad_hwnd)
        print(f"是否在虚拟屏幕上：{is_on_virtual}")
    else:
        print("未找到记事本窗口")
