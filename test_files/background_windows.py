# -*- coding: utf-8 -*-
"""
自定义Windows设备类，实现基于窗口消息的后台点击
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
from performance_monitor import performance_monitor

# 配置日志系统
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
        # 点击方式配置：'postmessage' 或 'sendinput'
        self.click_method = 'postmessage'
        # PostMessage 失败计数器
        self.postmessage_fail_count = 0
        # 最大失败次数，超过后切换到 SendInput
        self.max_postmessage_failures = 3
        # SendInput 是否恢复鼠标位置
        self.sendinput_restore_pos = True
    
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
        
        try:
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
        except pywintypes.error as e:
            logger.error(f"获取窗口父句柄失败：{e}")
            self.is_embedded = False
            self.embedded_hwnd = None
        
        try:
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
        except Exception as e:
            logger.error(f"检查窗口显示器失败：{e}")
            self.is_virtual_screen = False
            self.window_display = virtual_display_manager.get_main_display()
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
    
    def snapshot(self, filename=None, quality=10, max_size=None, **kwargs):
        """
        获取窗口截图 (严格禁止抢焦点)
        """
        logger.debug(f"调用snapshot方法，filename={filename}, hwnd={self.hwnd}")
        
        if not self.hwnd:
            logger.error("❌ 截图失败：未设置窗口句柄")
            return None
        
        try:
            # 优先尝试 PrintWindow (支持后台/遮挡截图)
            screen = self._snapshot_printwindow()
            
            if screen is None:
                # 降级到 mss 截图 (仅支持可见窗口)
                screen = self._snapshot_mss()
            
            if screen is None:
                logger.error("❌ 所有截图方法均失败 (窗口可能已最小化或被系统保护)")
                return None
                
            # 保存图片（如果需要）
            if filename:
                import aircv
                aircv.imwrite(filename, screen, quality, max_size=max_size)
                logger.debug(f"已保存截图到：{filename}")
            
            return screen
            
        except Exception as e:
            logger.error(f"截图失败：{e}", exc_info=True)
            return None

    def _snapshot_printwindow(self):
        """
        使用 PrintWindow API 进行后台截图
        """
        try:
            import win32ui
            import win32gui
            import win32con
            import cv2
            import numpy as np
            
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                return None
                
            # 创建设备上下文
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 使用 PrintWindow 截图
            # 0x00000002 = PW_RENDERFULLCONTENT (Win8.1+)
            # 直接使用 windll.user32，不需要 ctypes.windll
            result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 2)
            if result == 0:
                # 如果失败，尝试不带标志
                result = windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 0)
            
            if result == 0:
                logger.error("PrintWindow API 调用失败")
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwndDC)
                return None
                
            # 获取位图数据
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 转换为 numpy 数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwndDC)
            
            # 转换颜色空间 (BGRA -> BGR -> RGB)
            # Airtest 需要 RGB 格式，OpenCV 默认读取是 BGR
            # 注意：PrintWindow 截出来的是 BGRA
            img = img[..., :3]  # 去除 Alpha 通道
            img = img[..., ::-1] # BGR 转 RGB
            
            return img
            
        except Exception as e:
            logger.error(f"PrintWindow 截图异常: {e}")
            return None

    def _snapshot_mss(self):
        """
        使用 mss 进行屏幕截图 (仅适用于前台/可见窗口)
        """
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
            logger.error(f"mss 截图异常: {e}")
            return None
    
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
    
    def _get_client_coords(self, pos):
        """
        获取客户区坐标
        Args:
            pos: Airtest坐标 (相对于窗口左上角)
        Returns:
            (x, y): 客户区坐标
        """
        try:
            # 获取窗口位置
            window_rect = win32gui.GetWindowRect(self.hwnd)
            window_left, window_top = window_rect[0], window_rect[1]
            
            # 获取屏幕坐标
            if isinstance(pos, (list, tuple)):
                rel_x, rel_y = pos
                screen_x = window_left + rel_x
                screen_y = window_top + rel_y
            elif hasattr(pos, 'match_result') and pos.match_result:
                rel_x, rel_y = pos.match_result['result']
                screen_x = window_left + rel_x
                screen_y = window_top + rel_y
            else:
                rel_x, rel_y = tuple(pos)
                screen_x = window_left + rel_x
                screen_y = window_top + rel_y
                
            # 转换为客户区坐标
            point = win32gui.ScreenToClient(self.hwnd, (int(screen_x), int(screen_y)))
            return point
        except Exception as e:
            logger.error(f"坐标转换失败: {e}")
            return (0, 0)

    def swipe(self, t1, t2, duration=0.5, steps=5, **kwargs):
        """
        后台滑动实现 (禁止物理鼠标回退)
        """
        if not self.hwnd:
            logger.error("❌ 滑动失败：无窗口句柄")
            return False
            
        try:
            # 转换坐标
            if self.is_embedded:
                # 嵌入窗口直接使用坐标 (假设已经是客户区坐标)
                # 这里简化处理，实际可能需要更复杂的转换
                x1, y1 = self._get_embedded_window_coords(t1)
                x2, y2 = self._get_embedded_window_coords(t2)
            else:
                x1, y1 = self._get_client_coords(t1)
                x2, y2 = self._get_client_coords(t2)
            
            logger.info(f"后台滑动: ({x1}, {y1}) -> ({x2}, {y2}), duration={duration}")
            
            # 发送按下消息
            l_param = y1 << 16 | x1
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            
            # 计算每一步的间隔
            if steps < 1: steps = 1
            interval = duration / steps
            dx = (x2 - x1) / steps
            dy = (y2 - y1) / steps
            
            for i in range(steps):
                cx = int(x1 + dx * (i + 1))
                cy = int(y1 + dy * (i + 1))
                l_param = cy << 16 | cx
                win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, l_param)
                time.sleep(interval)
                
            # 发送释放消息
            l_param = y2 << 16 | x2
            win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 后台滑动异常: {e}")
            # 绝对不调用 super().swipe() !!!
            return False

    def touch(self, pos, duration=0.1, right_click=False, steps=1, **kwargs):
        """
        后台点击实现
        """
        if not self.hwnd:
            logger.error("❌ 点击失败：无窗口句柄")
            return False
        
        try:
            # 1. 获取窗口屏幕位置
            window_rect = win32gui.GetWindowRect(self.hwnd)
            window_left, window_top = window_rect[0], window_rect[1]
            
            # 2. 解析 Airtest 传入的坐标 (得到屏幕绝对坐标)
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
            
            # 3. 特殊处理 (-1, -1) 坐标：点击窗口中心
            if pos == (-1, -1) or pos == [-1, -1]:
                width = window_rect[2] - window_rect[0]
                height = window_rect[3] - window_rect[1]
                screen_x = window_left + width // 2
                screen_y = window_top + height // 2
                logger.info(f"触摸操作 - 自动定位到窗口中心: ({screen_x}, {screen_y})")
            
            # 4. 【关键】坐标转换 (Screen -> Client)
            try:
                # 使用 API 转换
                point = win32gui.ScreenToClient(self.hwnd, (int(screen_x), int(screen_y)))
                client_x, client_y = point[0], point[1]
                
                # 【调试日志】打印转换前后的坐标，帮你判断是否偏了
                logger.info(f"坐标调试: 相对({int(rel_x)},{int(rel_y)}) -> 屏幕({int(screen_x)},{int(screen_y)}) -> 客户区({client_x},{client_y})")
                
            except Exception as e:
                logger.error(f"坐标转换失败: {e}")
                return False
            
            # 5. 执行点击
            if self.click_method == 'postmessage':
                # 验证坐标是否有效
                if client_x < 0 or client_y < 0:
                    logger.warning(f"⚠️ 警告：计算出的客户区坐标为负数 ({client_x}, {client_y})")
                
                # 修改 2：确保 duration 至少为 0.05，防止传入过小的值
                safe_duration = max(duration, 0.05)
                logger.info(f"PostMessage 点击 -> 客户区({client_x}, {client_y}), 持续: {safe_duration}s")
                
                return self._send_click_message((client_x, client_y), safe_duration, right_click)
            
            elif self.click_method == 'sendinput':
                return self.independent_mouse.click_background_fallback(int(screen_x), int(screen_y), right_click, self.sendinput_restore_pos)
            
        except Exception as e:
            logger.error(f"❌ 后台点击异常：{e}", exc_info=True)
            # 绝对不调用 super().touch() !!!
            return False
    
    def _send_click_message(self, pos, duration=0.1, right_click=False):
        """
        发送窗口消息实现点击 (增强版：伪造激活状态 + 悬停模拟)
        Args:
            pos: 点击位置（客户区坐标）
            duration: 点击持续时间
            right_click: 是否右键点击
        Returns:
            bool: 是否成功
        """
        x, y = pos
        
        try:
            # 构建坐标参数
            l_param = y << 16 | x
            
            # 【关键修改 1】伪造窗口激活状态
            # 告诉窗口："嘿，你现在是活动窗口！"
            # WA_ACTIVE = 1
            win32gui.PostMessage(self.hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
            win32gui.PostMessage(self.hwnd, win32con.WM_NCACTIVATE, 1, 0)
            
            # 【关键修改 2】模拟鼠标悬停 (Hover)
            # 很多游戏按钮需要先检测到鼠标悬停，才会响应点击
            win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, 0, l_param)
            time.sleep(0.05) # 给游戏一点反应时间
            
            # 发送鼠标按下
            if right_click:
                win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, l_param)
            else:
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
            
            # 保持按住
            time.sleep(duration)
            
            # 发送鼠标释放
            if right_click:
                win32gui.PostMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, l_param)
            else:
                win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, l_param)
            
            return True
        except Exception as e:
            logger.error(f"发送窗口消息失败：{e}")
            return False
    
    def _send_input_click(self, screen_x, screen_y, duration=0.01, right_click=False):
        """
        使用 SendInput 实现点击（鼠标瞬移方案）
        Args:
            screen_x: 屏幕x坐标
            screen_y: 屏幕y坐标
            duration: 点击持续时间
            right_click: 是否右键点击
        Returns:
            bool: 是否成功
        """
        try:
            # 使用独立鼠标控制器的瞬移点击方法
            return self.independent_mouse.click_background_fallback(screen_x, screen_y, right_click)
        except Exception as e:
            logger.error(f"SendInput 点击失败：{e}")
            return False
    
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