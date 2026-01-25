# -*- coding: utf-8 -*-
"""
鼠标控制器
封装 Win32 API 实现鼠标点击和移动
"""

import win32gui
import win32api
import win32con
import time
import random

class MouseController:
    def __init__(self):
        pass
    
    def click(self, window_x, window_y, hwnd):
        """
        点击窗口相对坐标
        :param window_x: 窗口相对 X 坐标
        :param window_y: 窗口相对 Y 坐标
        :param hwnd: 窗口句柄
        """
        # 获取窗口客户区的屏幕坐标
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
        
        # 计算屏幕绝对坐标
        screen_x = left + window_x
        screen_y = top + window_y
        
        # 移动鼠标到目标位置（带拟人化轨迹）
        self._move_to(screen_x, screen_y)
        
        # 随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        
        # 执行点击
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
        
        # 点击后随机延迟
        time.sleep(random.uniform(0.1, 0.2))
    
    def _move_to(self, target_x, target_y):
        """
        带拟人化轨迹的鼠标移动
        :param target_x: 目标 X 坐标
        :param target_y: 目标 Y 坐标
        """
        # 获取当前鼠标位置
        current_x, current_y = win32api.GetCursorPos()
        
        # 计算距离
        distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
        
        # 根据距离计算移动步数
        steps = max(5, min(20, int(distance / 10)))
        
        # 生成移动轨迹
        for i in range(steps + 1):
            # 线性插值
            t = i / steps
            # 添加微小随机偏移，模拟人手抖动
            x = int(current_x + (target_x - current_x) * t + random.uniform(-2, 2))
            y = int(current_y + (target_y - current_y) * t + random.uniform(-2, 2))
            
            # 移动鼠标
            win32api.SetCursorPos((x, y))
            
            # 每步的延迟
            time.sleep(random.uniform(0.01, 0.03))
    
    def double_click(self, window_x, window_y, hwnd):
        """
        双击窗口相对坐标
        :param window_x: 窗口相对 X 坐标
        :param window_y: 窗口相对 Y 坐标
        :param hwnd: 窗口句柄
        """
        # 获取窗口客户区的屏幕坐标
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
        
        # 计算屏幕绝对坐标
        screen_x = left + window_x
        screen_y = top + window_y
        
        # 移动鼠标到目标位置
        self._move_to(screen_x, screen_y)
        
        # 随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        
        # 执行双击
        for _ in range(2):
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, screen_x, screen_y, 0, 0)
            time.sleep(random.uniform(0.05, 0.1))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, screen_x, screen_y, 0, 0)
            time.sleep(random.uniform(0.05, 0.1))
        
        # 双击后随机延迟
        time.sleep(random.uniform(0.1, 0.2))
    
    def right_click(self, window_x, window_y, hwnd):
        """
        右键点击窗口相对坐标
        :param window_x: 窗口相对 X 坐标
        :param window_y: 窗口相对 Y 坐标
        :param hwnd: 窗口句柄
        """
        # 获取窗口客户区的屏幕坐标
        rect = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (rect[0], rect[1]))
        
        # 计算屏幕绝对坐标
        screen_x = left + window_x
        screen_y = top + window_y
        
        # 移动鼠标到目标位置
        self._move_to(screen_x, screen_y)
        
        # 随机延迟
        time.sleep(random.uniform(0.1, 0.3))
        
        # 执行右键点击
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, screen_x, screen_y, 0, 0)
        time.sleep(random.uniform(0.05, 0.15))
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, screen_x, screen_y, 0, 0)
        
        # 点击后随机延迟
        time.sleep(random.uniform(0.1, 0.2))

# 单例模式
mouse_controller = MouseController()
