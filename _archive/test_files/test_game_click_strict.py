# -*- coding: utf-8 -*-
"""
游戏鼠标点击拦截测试脚本 - 严谨版
根据Gemini 3 Pro的建议，实现更严谨的测试方法
"""

import time
import sys
import os
from airtest.core.api import *
from airtest.core.settings import Settings as ST

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入win32相关模块
import win32gui
import win32con
import win32api

# 设置Airtest全局参数
ST.THRESHOLD = 0.7
ST.OPDELAY = 0.5

# 屏幕正中央坐标
CENTER_X, CENTER_Y = 960, 540

def get_game_window_hwnd():
    """
    获取游戏窗口句柄
    用户需要在游戏窗口最大化的情况下运行此脚本
    """
    print("\n正在检测当前活动窗口...")
    
    # 获取当前活动窗口句柄
    hwnd = win32gui.GetForegroundWindow()
    
    if hwnd:
        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)
        print(f"✓ 检测到活动窗口：{title}")
        print(f"  窗口句柄：{hwnd}")
        
        # 获取窗口位置和大小
        window_rect = win32gui.GetWindowRect(hwnd)
        print(f"  窗口位置：{window_rect}")
        print(f"  窗口大小：{window_rect[2]-window_rect[0]}x{window_rect[3]-window_rect[1]}")
        
        # 确认窗口是否最大化
        try:
            # 使用GetWindowPlacement检查窗口状态
            placement = win32gui.GetWindowPlacement(hwnd)
            # 0: SW_SHOWNORMAL, 1: SW_SHOWMINIMIZED, 2: SW_SHOWMAXIMIZED
            if placement[1] == 2:
                print("  ✓ 窗口已最大化")
            else:
                print("  ⚠ 窗口未最大化，建议最大化后重新测试")
        except Exception as e:
            print(f"  ⚠ 无法检查窗口状态: {e}")
        
        return hwnd, title
    else:
        print("✗ 未检测到活动窗口")
        return None, None

def test_postmessage_click(hwnd, screen_x, screen_y):
    """
    使用PostMessage方法点击，确保坐标转换正确
    Args:
        hwnd: 目标窗口句柄
        screen_x: 屏幕x坐标
        screen_y: 屏幕y坐标
    """
    print("\n1. 测试PostMessage方法：")
    print(f"   屏幕坐标: ({screen_x}, {screen_y})")
    
    try:
        # 转换屏幕坐标到窗口客户区坐标
        # 使用ScreenToClient API确保精确转换
        client_point = win32gui.ScreenToClient(hwnd, (screen_x, screen_y))
        client_x, client_y = client_point[0], client_point[1]
        
        print(f"   转换后客户区坐标: ({client_x}, {client_y})")
        
        # 构建lParam参数
        l_param = client_y << 16 | client_x
        
        print("   发送鼠标消息序列：")
        
        # 1. 发送鼠标移动消息
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEMOVE, 0, l_param)
        print("   ✓ 发送 WM_MOUSEMOVE")
        
        # 2. 发送鼠标左键按下消息
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        print("   ✓ 发送 WM_LBUTTONDOWN")
        
        # 3. 等待短暂时间（模拟真实点击）
        time.sleep(0.1)
        
        # 4. 发送鼠标左键释放消息
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
        print("   ✓ 发送 WM_LBUTTONUP")
        
        # 5. 发送鼠标离开消息
        win32gui.PostMessage(hwnd, win32con.WM_MOUSELEAVE, 0, 0)
        print("   ✓ 发送 WM_MOUSELEAVE")
        
        return True, "PostMessage方法执行完成"
        
    except Exception as e:
        print(f"   ✗ PostMessage方法失败: {e}")
        return False, str(e)

def test_sendinput_click(screen_x, screen_y):
    """
    使用SendInput方法点击（鼠标瞬移）
    Args:
        screen_x: 屏幕x坐标
        screen_y: 屏幕y坐标
    """
    print("\n2. 测试SendInput方法：")
    print(f"   屏幕坐标: ({screen_x}, {screen_y})")
    
    try:
        # 使用Airtest的touch方法，它内部使用SendInput
        touch((screen_x, screen_y))
        print("   ✓ SendInput方法执行完成")
        return True, "SendInput方法执行完成"
    except Exception as e:
        print(f"   ✗ SendInput方法失败: {e}")
        return False, str(e)

def main():
    print("=" * 60)
    print("游戏鼠标点击拦截测试脚本 - 严谨版")
    print("=" * 60)
    print("\n使用说明：")
    print("1. 请先打开游戏窗口并最大化")
    print("2. 确保游戏窗口是当前活动窗口")
    print("3. 运行此脚本，脚本会自动检测当前活动窗口")
    print("4. 观察游戏中的点击特效或反馈")
    print("\n测试流程：")
    print("- 每次测试会在屏幕正中央点击")
    print("- 先测试PostMessage方法，等待3秒观察效果")
    print("- 再测试SendInput方法，等待3秒观察效果")
    print("- 可以多次循环测试")
    print("\n按 Ctrl+C 可以停止测试")
    print("=" * 60)
    
    # 初始化Airtest设备
    print("\n正在初始化Airtest设备...")
    try:
        auto_setup(__file__, devices=["Windows:///"])
        print("✓ Airtest设备初始化成功")
    except Exception as e:
        print(f"✗ Airtest设备初始化失败: {e}")
        return
    
    # 获取游戏窗口句柄
    hwnd, title = get_game_window_hwnd()
    if not hwnd:
        print("\n✗ 无法获取游戏窗口句柄，请确保游戏窗口已打开并最大化")
        return
    
    # 等待用户准备
    input("\n按 Enter 键开始测试...")
    
    try:
        # 循环10次测试
        for test_count in range(1, 11):
            print(f"\n" + "=" * 50)
            print(f"测试 #{test_count}/10 - 屏幕正中央 ({CENTER_X}, {CENTER_Y})")
            print("=" * 50)
            
            # 1. 测试PostMessage方法
            success, result = test_postmessage_click(hwnd, CENTER_X, CENTER_Y)
            
            # 等待3秒观察效果
            print("\n   等待3秒，观察PostMessage方法效果...")
            time.sleep(3)
            
            # 2. 测试SendInput方法
            success, result = test_sendinput_click(CENTER_X, CENTER_Y)
            
            # 等待3秒观察效果
            print("\n   等待3秒，观察SendInput方法效果...")
            time.sleep(3)
            
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("测试已停止")
        print("=" * 60)
        print(f"\n总测试次数: {test_count}")
        print("\n测试结果分析：")
        print("1. 如果PostMessage方法有效：游戏接受Windows消息队列的鼠标事件")
        print("2. 如果只有SendInput方法有效：游戏绕过Windows消息队列，直接读取硬件数据")
        print("3. 如果两种方法都无效：可能是坐标问题或游戏防护机制很强")
        print("\n建议：")
        print("- 对于不支持PostMessage的游戏，建议使用基于虚拟屏幕的\"鼠标瞬移法\"")
        print("- 具体实现：记录当前鼠标位置→瞬移到虚拟屏幕目标坐标→执行点击→恢复原位置")
        print("=" * 60)

if __name__ == "__main__":
    main()
