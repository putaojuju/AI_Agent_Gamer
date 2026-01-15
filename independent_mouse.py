# -*- coding: utf-8 -*-
"""
独立鼠标控制模块
实现鼠标钩子和屏幕感知鼠标处理，确保虚拟屏幕的鼠标操作不影响主屏幕
"""

import win32gui
import win32con
import win32api
import ctypes
import logging
from ctypes import wintypes
from virtual_display import virtual_display_manager

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('independent_mouse.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('independent_mouse')

# 定义Windows API函数和类型
huser32 = ctypes.WinDLL('user32', use_last_error=True)

# 鼠标钩子回调类型
# 在较新版本的Python中，c_wparam和c_lparam已被移除，使用c_size_t替代
HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_size_t, ctypes.c_size_t)

# 鼠标事件结构
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulonglong),  # 使用c_ulonglong替代ULONG_PTR
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

# 鼠标事件标志
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
    实现鼠标钩子和屏幕感知鼠标处理
    """
    
    def __init__(self):
        """
        初始化独立鼠标控制器
        """
        self.hook_handle = None
        self.hook_callback = None
        self.is_hook_installed = False
        self.current_display = None
        self.virtual_mouse_pos = (0, 0)  # 虚拟鼠标位置
        self.target_display = None  # 当前目标显示器
        
        # 更新显示器信息
        virtual_display_manager.update_displays_info()
        self.main_display = virtual_display_manager.get_main_display()
        self.virtual_display = virtual_display_manager.get_virtual_display()
        
        logger.info("独立鼠标控制器已初始化")
    
    def install_mouse_hook(self):
        """
        安装鼠标钩子
        Returns:
            bool: 是否安装成功
        """
        try:
            # 定义鼠标钩子回调函数
            def mouse_hook_proc(nCode, wParam, lParam):
                if nCode >= 0:
                    # 获取当前活动窗口
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd:
                        # 获取窗口所在的显示器
                        window_display = virtual_display_manager.get_window_display(hwnd)
                        self.current_display = window_display
                        
                        # 如果窗口在主屏幕，允许正常鼠标操作
                        if window_display['is_primary']:
                            # 主屏幕操作，不拦截
                            pass
                        else:
                            # 虚拟屏幕操作，处理鼠标事件
                            # 这里可以添加自定义处理逻辑
                            pass
                
                # 调用下一个钩子
                return huser32.CallNextHookEx(self.hook_handle, nCode, wParam, lParam)
            
            # 创建钩子回调
            self.hook_callback = HOOKPROC(mouse_hook_proc)
            
            # 安装钩子
            self.hook_handle = huser32.SetWindowsHookExW(
                win32con.WH_MOUSE_LL,  # 低级鼠标钩子
                self.hook_callback,
                None,
                0
            )
            
            if not self.hook_handle:
                raise ctypes.WinError(ctypes.get_last_error())
            
            self.is_hook_installed = True
            logger.info("鼠标钩子已安装")
            return True
        except Exception as e:
            logger.error(f"安装鼠标钩子失败: {e}")
            self.is_hook_installed = False
            return False
    
    def uninstall_mouse_hook(self):
        """
        卸载鼠标钩子
        Returns:
            bool: 是否卸载成功
        """
        try:
            if self.hook_handle:
                huser32.UnhookWindowsHookEx(self.hook_handle)
                self.hook_handle = None
                self.hook_callback = None
                self.is_hook_installed = False
                logger.info("鼠标钩子已卸载")
                return True
            return False
        except Exception as e:
            logger.error(f"卸载鼠标钩子失败: {e}")
            return False
    
    def set_target_display(self, display):
        """
        设置目标显示器
        Args:
            display: 目标显示器信息字典或显示器ID
        """
        if isinstance(display, dict):
            self.target_display = display
        elif isinstance(display, int):
            # 根据ID查找显示器
            displays = virtual_display_manager.get_displays()
            for d in displays:
                if d['id'] == display:
                    self.target_display = d
                    break
        
        if self.target_display:
            logger.info(f"目标显示器已设置为: {self.target_display['id']}")
        else:
            logger.warning("未找到指定的目标显示器")
    
    def set_target_display_to_virtual(self):
        """
        将目标显示器设置为虚拟屏幕
        """
        self.target_display = self.virtual_display
        if self.virtual_display:
            logger.info(f"目标显示器已设置为虚拟屏幕: {self.virtual_display['id']}")
    
    def set_target_display_to_main(self):
        """
        将目标显示器设置为主屏幕
        """
        self.target_display = self.main_display
        logger.info(f"目标显示器已设置为主屏幕: {self.main_display['id']}")
    
    def send_mouse_input(self, dx, dy, dwFlags, mouseData=0):
        """
        发送鼠标输入事件
        Args:
            dx: x坐标偏移
            dy: y坐标偏移
            dwFlags: 鼠标事件标志
            mouseData: 鼠标数据
        Returns:
            bool: 是否发送成功
        """
        try:
            # 如果没有设置目标显示器，使用当前活动窗口的显示器
            if not self.target_display:
                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    self.target_display = virtual_display_manager.get_window_display(hwnd)
                else:
                    self.target_display = self.main_display
            
            # 创建鼠标输入结构
            mi = MOUSEINPUT()
            
            if dwFlags & MOUSEEVENTF_ABSOLUTE:
                # 绝对坐标，转换为虚拟屏幕坐标
                # 计算目标屏幕的绝对坐标（0-65535范围）
                screen_width = self.target_display['width']
                screen_height = self.target_display['height']
                
                # 确保坐标在有效范围内
                dx = max(0, min(dx, screen_width))
                dy = max(0, min(dy, screen_height))
                
                # 转换为SendInput使用的绝对坐标格式（0-65535）
                mi.dx = int((dx / screen_width) * 65535)
                mi.dy = int((dy / screen_height) * 65535)
            else:
                # 相对坐标，直接使用
                mi.dx = dx
                mi.dy = dy
            
            mi.mouseData = mouseData
            mi.dwFlags = dwFlags
            mi.time = 0
            mi.dwExtraInfo = huser32.GetMessageExtraInfo()
            
            # 创建INPUT结构
            inp = INPUT()
            inp.type = INPUT_MOUSE
            inp.mi = mi
            
            # 发送输入
            nInputs = 1
            cbSize = ctypes.sizeof(INPUT)
            
            result = huser32.SendInput(nInputs, ctypes.byref(inp), cbSize)
            
            if result != nInputs:
                raise ctypes.WinError(ctypes.get_last_error())
            
            logger.debug(f"鼠标输入已发送: dx={dx}, dy={dy}, flags={dwFlags}, display={self.target_display['id']}")
            return True
        except Exception as e:
            logger.error(f"发送鼠标输入失败: {e}")
            return False
    
    def move_mouse(self, x, y, absolute=True):
        """
        移动鼠标到指定位置
        Args:
            x: x坐标
            y: y坐标
            absolute: 是否使用绝对坐标
        Returns:
            bool: 是否移动成功
        """
        dwFlags = MOUSEEVENTF_MOVE
        if absolute:
            dwFlags |= MOUSEEVENTF_ABSOLUTE
        
        return self.send_mouse_input(x, y, dwFlags)
    
    def click(self, x, y, right_click=False, absolute=True):
        """
        点击鼠标
        Args:
            x: x坐标
            y: y坐标
            right_click: 是否右键点击
            absolute: 是否使用绝对坐标
        Returns:
            bool: 是否点击成功
        """
        # 移动鼠标到目标位置
        if not self.move_mouse(x, y, absolute):
            return False
        
        # 发送点击事件
        down_flag = MOUSEEVENTF_RIGHTDOWN if right_click else MOUSEEVENTF_LEFTDOWN
        up_flag = MOUSEEVENTF_RIGHTUP if right_click else MOUSEEVENTF_LEFTUP
        
        if not self.send_mouse_input(0, 0, down_flag):
            return False
        
        # 短暂延迟
        win32api.Sleep(50)
        
        if not self.send_mouse_input(0, 0, up_flag):
            return False
        
        logger.debug(f"{right_click and '右键' or '左键'}点击已发送: ({x}, {y})")
        return True
    
    def get_virtual_mouse_pos(self):
        """
        获取虚拟鼠标位置
        Returns:
            tuple: 虚拟鼠标位置 (x, y)
        """
        return self.virtual_mouse_pos
    
    def update_display_info(self):
        """
        更新显示器信息
        """
        virtual_display_manager.update_displays_info()
        self.main_display = virtual_display_manager.get_main_display()
        self.virtual_display = virtual_display_manager.get_virtual_display()
        logger.info("显示器信息已更新")

# 单例模式
independent_mouse = IndependentMouse()

# 测试代码
if __name__ == "__main__":
    im = IndependentMouse()
    
    # 更新显示器信息
    im.update_display_info()
    
    # 设置目标显示器为虚拟屏幕
    im.set_target_display_to_virtual()
    
    # 测试鼠标移动和点击
    if im.virtual_display:
        # 在虚拟屏幕中心点击
        center_x = im.virtual_display['width'] // 2
        center_y = im.virtual_display['height'] // 2
        print(f"在虚拟屏幕中心 ({center_x}, {center_y}) 点击")
        im.click(center_x, center_y)
    else:
        print("未检测到虚拟屏幕，无法进行测试")
    
    # 安装鼠标钩子（可选，需要管理员权限）
    # if im.install_mouse_hook():
    #     print("鼠标钩子已安装，按Enter键卸载")
    #     input()
    #     im.uninstall_mouse_hook()
    # else:
    #     print("安装鼠标钩子失败")
