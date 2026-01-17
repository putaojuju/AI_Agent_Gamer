# -*- coding: utf-8 -*-
"""
虚拟屏幕管理模块
实现显示器信息获取、虚拟屏幕创建和管理功能
"""

import win32gui
import win32con
import win32api
import pywintypes
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('virtual_display.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('virtual_display')

class VirtualDisplayManager:
    """
    虚拟屏幕管理器
    负责虚拟屏幕的创建、管理和操作
    """
    
    def __init__(self):
        """
        初始化虚拟屏幕管理器
        """
        self.displays = []
        self.virtual_display = None
        self.main_display = None
        self.update_displays_info()
    
    def update_displays_info(self):
        """
        更新显示器信息
        """
        self.displays = []
        self.virtual_display = None
        self.main_display = None
        
        logger.info("开始检测显示器")
        
        # 由于win32gui.EnumDisplayDevices在某些Python环境中不存在，直接使用方法2
        method1_success = False
        logger.info("直接使用方法2获取主显示器信息")
        
        # 如果方法1失败，尝试使用GetSystemMetrics获取主显示器信息
        if not method1_success or len(self.displays) == 0:
            logger.info("方法1检测失败，尝试使用方法2获取主显示器信息")
            try:
                # 获取屏幕尺寸
                width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
                height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
                
                # 创建主显示器信息
                main_display_info = {
                    'id': 0,
                    'name': r'\.\DISPLAY1',
                    'device_string': '主显示器',
                    'is_primary': True,
                    'left': 0,
                    'top': 0,
                    'width': width,
                    'height': height,
                    'refresh_rate': 60,  # 假设默认刷新率
                    'bit_depth': 32,       # 假设默认位深度
                    'is_attached': True
                }
                
                self.displays.append(main_display_info)
                self.main_display = main_display_info
                
                logger.info(f"使用方法2获取主显示器信息成功: {width}x{height}")
            except Exception as e:
                logger.error(f"使用方法2获取主显示器信息失败: {e}")
        
        logger.info(f"检测到 {len(self.displays)} 个显示器")
        for display in self.displays:
            logger.debug(f"显示器 {display['id']}: {display['name']}, 位置: ({display['left']}, {display['top']}), 大小: {display['width']}x{display['height']}, 主屏幕: {display['is_primary']}, 已连接: {display.get('is_attached', True)}")
        
        # 如果没有找到虚拟屏幕，尝试创建一个默认的虚拟屏幕
        if not self.virtual_display and self.main_display:
            logger.info("没有检测到虚拟屏幕，尝试创建默认虚拟屏幕")
            # 假设虚拟屏幕位于主屏幕右侧
            default_virtual_display = {
                'id': len(self.displays),
                'name': r'\.\DISPLAY2',
                'device_string': '默认虚拟屏幕',
                'is_primary': False,
                'left': self.main_display['width'],
                'top': 0,
                'width': self.main_display['width'],
                'height': self.main_display['height'],
                'refresh_rate': self.main_display['refresh_rate'],
                'bit_depth': self.main_display['bit_depth'],
                'is_attached': False
            }
            self.displays.append(default_virtual_display)
            self.virtual_display = default_virtual_display
            logger.info(f"创建默认虚拟屏幕: {default_virtual_display['width']}x{default_virtual_display['height']}")
    
    def get_displays(self):
        """
        获取所有显示器信息
        Returns:
            list: 显示器信息列表
        """
        return self.displays
    
    def get_main_display(self):
        """
        获取主屏幕信息
        Returns:
            dict: 主屏幕信息
        """
        return self.main_display
    
    def get_virtual_display(self):
        """
        获取虚拟屏幕信息
        Returns:
            dict: 虚拟屏幕信息，如果没有则返回None
        """
        return self.virtual_display
    
    def is_point_in_display(self, point, display):
        """
        判断点是否在指定显示器内
        Args:
            point: 点坐标 (x, y)
            display: 显示器信息字典
        Returns:
            bool: 点是否在显示器内
        """
        x, y = point
        return (display['left'] <= x < display['left'] + display['width'] and
                display['top'] <= y < display['top'] + display['height'])
    
    def get_window_display(self, hwnd):
        """
        获取窗口所在的显示器
        Args:
            hwnd: 窗口句柄
        Returns:
            dict: 窗口所在的显示器信息
        """
        try:
            # 首先检查窗口句柄是否有效
            if not win32gui.IsWindow(hwnd):
                logger.error(f"无效的窗口句柄: {hwnd}")
                return self.main_display
            
            # 获取窗口矩形
            rect = win32gui.GetWindowRect(hwnd)
            # 计算窗口中心点
            center_x = (rect[0] + rect[2]) // 2
            center_y = (rect[1] + rect[3]) // 2
            
            # 查找包含窗口中心点的显示器
            for display in self.displays:
                if self.is_point_in_display((center_x, center_y), display):
                    return display
            
            # 如果没有找到，返回主屏幕
            return self.main_display
        except pywintypes.error as e:
            logger.error(f"获取窗口 {hwnd} 所在显示器失败: {e}")
            return self.main_display
        except Exception as e:
            logger.error(f"获取窗口 {hwnd} 所在显示器失败: {e}")
            return self.main_display
    
    def move_window_to_display(self, hwnd, display):
        """
        将窗口移动到指定显示器
        Args:
            hwnd: 窗口句柄
            display: 目标显示器信息字典
        Returns:
            bool: 是否移动成功
        """
        try:
            # 调整窗口大小和位置到目标显示器
            win32gui.MoveWindow(
                hwnd,
                display['left'], display['top'],
                display['width'], display['height'],
                True
            )
            logger.info(f"窗口 {hwnd} 已移动到显示器 {display['id']}")
            return True
        except Exception as e:
            logger.error(f"移动窗口 {hwnd} 到显示器 {display['id']} 失败: {e}")
            return False
    
    def move_window_to_virtual_display(self, hwnd):
        """
        将窗口移动到虚拟屏幕
        Args:
            hwnd: 窗口句柄
        Returns:
            bool: 是否移动成功
        """
        if not self.virtual_display:
            logger.error("未检测到虚拟屏幕")
            return False
        
        return self.move_window_to_display(hwnd, self.virtual_display)
    
    def activate_window(self, hwnd):
        """
        激活窗口，使其获得焦点
        Args:
            hwnd: 窗口句柄
        Returns:
            bool: 是否激活成功
        """
        try:
            # 确保窗口可见
            win32gui.ShowWindow(hwnd, win32con.SW_SHOWMAXIMIZED)
            # 激活窗口
            win32gui.SetForegroundWindow(hwnd)
            logger.info(f"窗口 {hwnd} 已激活")
            return True
        except Exception as e:
            logger.error(f"激活窗口 {hwnd} 失败: {e}")
            return False
    
    def find_window_by_title(self, title, exact_match=False):
        """
        根据标题查找窗口
        Args:
            title: 窗口标题
            exact_match: 是否精确匹配
        Returns:
            int: 窗口句柄，如果没有找到则返回0
        """
        if exact_match:
            return win32gui.FindWindow(None, title)
        else:
            # 模糊匹配，遍历所有窗口
            matching_windows = []
            
            def enum_windows_proc(hwnd, lparam):
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    if title in window_title:
                        matching_windows.append(hwnd)
                return True
            
            win32gui.EnumWindows(enum_windows_proc, None)
            return matching_windows[0] if matching_windows else 0
    
    def get_window_title(self, hwnd):
        """
        获取窗口标题
        Args:
            hwnd: 窗口句柄
        Returns:
            str: 窗口标题
        """
        return win32gui.GetWindowText(hwnd)

# 单例模式
virtual_display_manager = VirtualDisplayManager()

# 测试代码
if __name__ == "__main__":
    vdm = VirtualDisplayManager()
    displays = vdm.get_displays()
    
    print(f"检测到 {len(displays)} 个显示器:")
    for display in displays:
        print(f"  显示器 {display['id']}: {display['name']}")
        print(f"    位置: ({display['left']}, {display['top']})")
        print(f"    大小: {display['width']}x{display['height']}")
        print(f"    刷新率: {display['refresh_rate']}Hz")
        print(f"    颜色深度: {display['bit_depth']}位")
        print(f"    主屏幕: {display['is_primary']}")
    
    main_display = vdm.get_main_display()
    virtual_display = vdm.get_virtual_display()
    
    if main_display:
        print(f"\n主屏幕: 显示器 {main_display['id']}")
    
    if virtual_display:
        print(f"虚拟屏幕: 显示器 {virtual_display['id']}")
    else:
        print("\n未检测到虚拟屏幕，请先安装虚拟显示驱动")
