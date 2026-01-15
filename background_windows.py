# -*- coding: utf-8 -*-
"""
自定义Windows设备类，实现基于窗口消息的后台点击
不影响前台操作，支持真正的后台运行
支持虚拟屏幕和独立鼠标控制
"""

import time
import win32gui
import win32con
import win32api
import logging
from airtest.core.win.win import Windows
from virtual_display import virtual_display_manager
from independent_mouse import independent_mouse

# 配置日志系统
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('background_windows.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('background_windows')

class BackgroundWindows(Windows):
    """
    自定义Windows设备类，使用窗口消息机制实现后台点击
    不影响前台操作，支持真正的后台运行
    """
    
    def __init__(self, device):
        """
        初始化后台设备
        Args:
            device: 已经初始化的Windows设备实例
        """
        # 不需要调用父类的__init__，直接复制已有设备的属性
        self.__dict__ = device.__dict__.copy()
        # 添加窗口句柄属性，用于后台操作
        self.hwnd = None
        # 保存原始设备，用于失败时降级
        self.original_device = device
        # 添加嵌入窗口标记
        self.is_embedded = False
        # 保存嵌入窗口句柄
        self.embedded_hwnd = None
        # 添加虚拟屏幕相关属性
        self.is_virtual_screen = False
        # 保存窗口所在的显示器
        self.window_display = None
        # 独立鼠标控制器
        self.independent_mouse = independent_mouse
    
    def init_hwnd(self, hwnd):
        """
        初始化窗口句柄
        Args:
            hwnd: 目标窗口句柄
        """
        self.hwnd = hwnd
        # 保存原始设备的窗口句柄（如果有）
        self.original_handle = getattr(self, 'handle', None)
        # 设置当前设备的窗口句柄
        self.handle = hwnd
        
        # 检查窗口是否为嵌入窗口
        parent_hwnd = win32gui.GetParent(hwnd)
        if parent_hwnd:
            self.is_embedded = True
            self.embedded_hwnd = hwnd
            logger.info(f"窗口 {hwnd} 是嵌入窗口，父窗口句柄：{parent_hwnd}")
        else:
            self.is_embedded = False
            self.embedded_hwnd = None
            logger.info(f"窗口 {hwnd} 不是嵌入窗口")
        
        # 检查窗口所在的显示器
        virtual_display_manager.update_displays_info()
        self.window_display = virtual_display_manager.get_window_display(hwnd)
        # 检查是否在虚拟屏幕上
        if self.window_display and not self.window_display['is_primary']:
            self.is_virtual_screen = True
            logger.info(f"窗口 {hwnd} 在虚拟屏幕上：显示器 {self.window_display['id']}")
            # 设置独立鼠标的目标显示器
            self.independent_mouse.set_target_display(self.window_display)
        else:
            self.is_virtual_screen = False
            logger.info(f"窗口 {hwnd} 在主屏幕上：显示器 {self.window_display['id']}")
            # 设置独立鼠标的目标显示器
            self.independent_mouse.set_target_display(self.window_display)
    
    def _get_screen_coords(self, pos):
        """
        获取屏幕坐标
        Args:
            pos: 点击位置
        Returns:
            屏幕坐标 (x, y)
        """
        # 如果是列表或元组，直接返回
        if isinstance(pos, (list, tuple)):
            return pos
        # 如果是Template对象，需要获取其坐标
        elif hasattr(pos, 'match_result') and pos.match_result:
            return pos.match_result['result']
        # 如果是dict对象，可能包含坐标信息
        elif isinstance(pos, dict):
            # 检查是否有x, y或result字段
            if 'x' in pos and 'y' in pos:
                return (pos['x'], pos['y'])
            elif 'result' in pos:
                return pos['result']
        # 其他情况，尝试转换为元组
        try:
            # 尝试转换为可迭代对象
            return tuple(pos)
        except (TypeError, ValueError):
            # 无法转换，直接返回
            return pos
    
    def _get_embedded_window_coords(self, pos):
        """
        获取嵌入窗口内的坐标
        Args:
            pos: 点击位置（Airtest直接提供的客户区坐标）
        Returns:
            嵌入窗口内的客户区坐标 (x, y)
        """
        if not self.hwnd:
            return self._get_screen_coords(pos)
        
        try:
            # Airtest脚本提供的坐标已经是客户区坐标，直接使用
            x, y = self._get_screen_coords(pos)
            
            # 获取窗口客户区大小
            client_rect = win32gui.GetClientRect(self.hwnd)
            client_width = client_rect[2]
            client_height = client_rect[3]
            
            # 确保坐标在客户区范围内
            client_x = max(0, min(x, client_width))
            client_y = max(0, min(y, client_height))
            
            return client_x, client_y
            
        except Exception as e:
            logger.error(f"嵌入窗口坐标转换失败：{e}")
            # 转换失败时返回原始坐标
            return self._get_screen_coords(pos)
    
    def touch(self, pos, duration=0.01, right_click=False, steps=1, **kwargs):
        """
        后台点击实现
        Args:
            pos: 点击位置
            duration: 点击持续时间
            right_click: 是否右键点击
            steps: 移动步数（后台模式下忽略）
            **kwargs: 其他参数
        """
        if not self.hwnd:
            # 如果没有窗口句柄，使用默认实现
            try:
                return super(BackgroundWindows, self).touch(pos, **kwargs)
            except Exception as e:
                logger.error(f"调用默认touch方法失败：{e}")
                return False
        
        try:
            # 坐标转换：将Airtest坐标转换为窗口客户区坐标
            logger.debug(f"触摸操作 - 原始坐标：{pos}")
            
            # 获取窗口客户区大小
            client_rect = win32gui.GetClientRect(self.hwnd)
            client_width = client_rect[2]
            client_height = client_rect[3]
            logger.debug(f"触摸操作 - 客户区大小：{client_width}x{client_height}")
            
            # 直接使用Airtest提供的坐标，确保它是相对客户区的
            if isinstance(pos, (list, tuple)):
                client_x, client_y = pos
                logger.debug(f"触摸操作 - 直接使用列表/元组坐标：({client_x}, {client_y})")
            elif hasattr(pos, 'match_result') and pos.match_result:
                client_x, client_y = pos.match_result['result']
                logger.debug(f"触摸操作 - 从match_result获取坐标：({client_x}, {client_y})")
            else:
                # 尝试转换为坐标
                try:
                    client_x, client_y = tuple(pos)
                    logger.debug(f"触摸操作 - 转换为元组坐标：({client_x}, {client_y})")
                except Exception as e:
                    logger.error(f"触摸操作 - 坐标转换失败：{e}")
                    return False
            
            # 确保坐标在客户区范围内
            client_x = max(0, min(int(client_x), client_width - 1))
            client_y = max(0, min(int(client_y), client_height - 1))
            logger.debug(f"触摸操作 - 调整后坐标：({client_x}, {client_y})")
            
            # 发送点击消息
            # 对于虚拟屏幕或嵌入窗口，使用独立鼠标控制器
            if self.is_virtual_screen or self.is_embedded:
                logger.info(f"触摸操作 - 使用独立鼠标控制器，点击位置：({client_x}, {client_y})")
                # 使用独立鼠标进行点击
                self.independent_mouse.click(client_x, client_y, right_click)
            else:
                logger.info(f"触摸操作 - 使用窗口消息方法，点击位置：({client_x}, {client_y})")
                self._send_click_message((client_x, client_y), duration, right_click)
            return True
        except Exception as e:
            logger.error(f"后台点击失败：{e}", exc_info=True)
            
            # 失败时不调用默认实现，避免影响前台
            return False
    
    def _send_click_message(self, pos, duration=0.01, right_click=False):
        """
        发送窗口消息实现点击
        Args:
            pos: 点击位置（客户区坐标）
            duration: 点击持续时间
            right_click: 是否右键点击
        """
        x, y = pos
        
        # 构建坐标参数
        l_param = y << 16 | x
        
        # 发送鼠标移动消息
        win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, l_param)
        
        # 发送鼠标按下消息
        if right_click:
            # 右键点击
            win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, l_param)
        else:
            # 左键点击
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        
        # 等待指定的点击持续时间
        time.sleep(duration)
        
        # 发送鼠标释放消息
        if right_click:
            win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, l_param)
        else:
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, l_param)
        
        # 发送鼠标离开消息，确保状态正确
        win32gui.PostMessage(self.hwnd, win32con.WM_MOUSELEAVE, 0, 0)
    
    def _send_double_click_message(self, pos):
        """
        发送窗口消息实现双击
        Args:
            pos: 点击位置（客户区坐标）
        """
        x, y = pos
        l_param = y << 16 | x
        
        # 发送双击消息
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDBLCLK, win32con.MK_LBUTTON, l_param)
    
    def _send_input_mouse(self, pos, duration=0.01, right_click=False):
        """
        使用win32api.SendInput实现鼠标点击
        Args:
            pos: 点击位置（客户区坐标）
            duration: 点击持续时间
            right_click: 是否右键点击
        """
        x, y = pos
        
        logger.debug(f"SendInput模拟点击 - 客户区坐标：({x}, {y})")
        
        # 获取窗口在屏幕上的位置
        window_rect = win32gui.GetWindowRect(self.hwnd)
        window_left, window_top, _, _ = window_rect
        
        # 转换为屏幕坐标
        screen_x = window_left + x
        screen_y = window_top + y
        
        # 保存当前鼠标位置
        current_pos = win32api.GetCursorPos()
        logger.debug(f"SendInput模拟点击 - 当前鼠标位置：{current_pos}")
        logger.debug(f"SendInput模拟点击 - 窗口位置：({window_left}, {window_top})")
        logger.debug(f"SendInput模拟点击 - 目标屏幕位置：({screen_x}, {screen_y})")
        
        try:
            # 将鼠标移动到目标位置
            win32api.SetCursorPos((screen_x, screen_y))
            time.sleep(0.01)  # 短暂延迟，确保鼠标移动完成
            
            # 按下鼠标按钮
            button = win32con.MOUSEEVENTF_RIGHTDOWN if right_click else win32con.MOUSEEVENTF_LEFTDOWN
            win32api.mouse_event(button, 0, 0, 0, 0)
            time.sleep(duration)  # 保持点击状态
            
            # 释放鼠标按钮
            button = win32con.MOUSEEVENTF_RIGHTUP if right_click else win32con.MOUSEEVENTF_LEFTUP
            win32api.mouse_event(button, 0, 0, 0, 0)
            time.sleep(0.01)  # 短暂延迟，确保鼠标释放完成
            
            # 恢复鼠标位置
            win32api.SetCursorPos(current_pos)
            logger.debug("SendInput模拟点击完成")
            return True
            
        except Exception as e:
            logger.error(f"SendInput模拟点击失败：{e}", exc_info=True)
            # 恢复鼠标位置
            win32api.SetCursorPos(current_pos)
            return False
    
    def _send_key_message(self, key_code, is_down=True):
        """
        发送键盘消息
        Args:
            key_code: 按键代码
            is_down: 是否按下（True）或释放（False）
        """
        if is_down:
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYDOWN, key_code, 0)
        else:
            win32gui.PostMessage(self.hwnd, win32con.WM_KEYUP, key_code, 0)
    
    def keyevent(self, keyname, **kwargs):
        """
        后台键盘事件实现
        Args:
            keyname: 按键名称
            **kwargs: 其他参数
        """
        if not self.hwnd:
            # 如果没有窗口句柄，使用默认实现
            return super(BackgroundWindows, self).keyevent(keyname, **kwargs)
        
        # 简单实现：将按键名称转换为虚拟键码
        # 这里只实现了部分常用按键，完整实现需要更复杂的映射
        key_map = {
            'a': 0x41,
            'b': 0x42,
            'c': 0x43,
            'd': 0x44,
            'e': 0x45,
            'f': 0x46,
            'g': 0x47,
            'h': 0x48,
            'i': 0x49,
            'j': 0x4A,
            'k': 0x4B,
            'l': 0x4C,
            'm': 0x4D,
            'n': 0x4E,
            'o': 0x4F,
            'p': 0x50,
            'q': 0x51,
            'r': 0x52,
            's': 0x53,
            't': 0x54,
            'u': 0x55,
            'v': 0x56,
            'w': 0x57,
            'x': 0x58,
            'y': 0x59,
            'z': 0x5A,
            '0': 0x30,
            '1': 0x31,
            '2': 0x32,
            '3': 0x33,
            '4': 0x34,
            '5': 0x35,
            '6': 0x36,
            '7': 0x37,
            '8': 0x38,
            '9': 0x39,
            'enter': 0x0D,
            'return': 0x0D,
            'backspace': 0x08,
            'tab': 0x09,
            'space': 0x20,
            'escape': 0x1B,
            'left': 0x25,
            'up': 0x26,
            'right': 0x27,
            'down': 0x28,
        }
        
        key_code = key_map.get(keyname.lower(), None)
        if key_code:
            # 发送键盘消息
            self._send_key_message(key_code, True)
            time.sleep(0.01)
            self._send_key_message(key_code, False)
            return True
        else:
            # 未知按键，使用默认实现
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
            # 如果没有窗口句柄，使用默认实现
            return super(BackgroundWindows, self).type(text, with_spaces, **kwargs)
        
        try:
            for char in text:
                # 发送字符消息
                win32gui.PostMessage(self.hwnd, win32con.WM_CHAR, ord(char), 0)
                time.sleep(0.01)  # 短暂延迟，模拟真实输入
            return True
        except Exception as e:
            logger.error(f"后台输入失败：{e}", exc_info=True)
            # 失败时使用默认实现
            logger.warning("后台输入失败，使用默认实现")
            return super(BackgroundWindows, self).type(text, with_spaces, **kwargs)