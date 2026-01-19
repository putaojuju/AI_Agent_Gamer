# -*- coding: utf-8 -*-
"""
游戏兼容性测试脚本
用于验证游戏是否支持 PostMessage 点击
根据 Gemini_advice.txt 的建议创建
"""

import win32gui
import win32con
import win32api
import time
import sys
import argparse

def test_postmessage_click(hwnd, x, y):
    """
    测试 PostMessage 点击是否有效
    Args:
        hwnd: 窗口句柄
        x: 窗口客户区x坐标
        y: 窗口客户区y坐标
    Returns:
        bool: PostMessage 是否有效
    """
    print(f"尝试使用 PostMessage 点击句柄 {hwnd} 坐标 ({x}, {y})")
    
    # 转换为 lParam
    l_param = (y << 16) | x
    
    try:
        # 发送鼠标按下消息
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        time.sleep(0.1)
        
        # 发送鼠标释放消息
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
        
        print("PostMessage 消息已发送")
        return True
    except Exception as e:
        print(f"PostMessage 发送失败：{e}")
        return False

def test_sendinput_click(hwnd, x, y):
    """
    测试 SendInput 点击（鼠标瞬移方案）
    Args:
        hwnd: 窗口句柄
        x: 窗口客户区x坐标
        y: 窗口客户区y坐标
    Returns:
        bool: SendInput 是否有效
    """
    print(f"尝试使用 SendInput 点击句柄 {hwnd} 坐标 ({x}, {y})")
    
    try:
        # 获取窗口在屏幕上的位置
        window_rect = win32gui.GetWindowRect(hwnd)
        screen_x = window_rect[0] + x
        screen_y = window_rect[1] + y
        
        # 保存当前鼠标位置
        original_pos = win32api.GetCursorPos()
        print(f"保存当前鼠标位置：{original_pos}")
        
        # 移动到目标位置
        win32api.SetCursorPos((screen_x, screen_y))
        time.sleep(0.01)
        
        # 物理点击
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.02)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        # 恢复鼠标位置
        win32api.SetCursorPos(original_pos)
        
        print("SendInput 点击已完成")
        return True
    except Exception as e:
        print(f"SendInput 点击失败：{e}")
        # 尝试恢复鼠标位置
        try:
            win32api.SetCursorPos(original_pos)
        except:
            pass
        return False

def main():
    parser = argparse.ArgumentParser(description='游戏兼容性测试脚本')
    parser.add_argument('--window-hwnd', type=int, help='窗口句柄')
    parser.add_argument('--window-title', type=str, help='窗口标题')
    parser.add_argument('--test-x', type=int, default=100, help='测试点击的X坐标')
    parser.add_argument('--test-y', type=int, default=100, help='测试点击的Y坐标')
    parser.add_argument('--test-method', type=str, default='both', 
                       choices=['postmessage', 'sendinput', 'both'],
                       help='测试方法：postmessage、sendinput 或 both')
    
    args = parser.parse_args()
    
    # 获取窗口句柄
    hwnd = None
    if args.window_hwnd:
        hwnd = args.window_hwnd
        print(f"使用指定的窗口句柄：{hwnd}")
    elif args.window_title:
        hwnd = win32gui.FindWindow(None, args.window_title)
        if hwnd == 0:
            print(f"错误：未找到窗口标题为 '{args.window_title}' 的窗口")
            return
        print(f"找到窗口句柄：{hwnd}")
    else:
        print("错误：必须指定 --window-hwnd 或 --window-title")
        return
    
    # 验证窗口句柄
    if not win32gui.IsWindow(hwnd):
        print(f"错误：窗口句柄 {hwnd} 无效")
        return
    
    # 获取窗口信息
    window_title = win32gui.GetWindowText(hwnd)
    window_rect = win32gui.GetWindowRect(hwnd)
    print(f"窗口标题：{window_title}")
    print(f"窗口位置：{window_rect}")
    
    # 测试点击
    test_x = args.test_x
    test_y = args.test_y
    
    print(f"\n开始测试点击坐标：({test_x}, {test_y})")
    print("=" * 60)
    
    if args.test_method in ['postmessage', 'both']:
        print("\n【测试 1：PostMessage 方法】")
        print("-" * 60)
        postmessage_result = test_postmessage_click(hwnd, test_x, test_y)
        print(f"PostMessage 测试结果：{'成功' if postmessage_result else '失败'}")
        print("\n请观察游戏是否有反应（按钮被点击等）")
        input("按 Enter 键继续...")
    
    if args.test_method in ['sendinput', 'both']:
        print("\n【测试 2：SendInput 方法（鼠标瞬移）】")
        print("-" * 60)
        sendinput_result = test_sendinput_click(hwnd, test_x, test_y)
        print(f"SendInput 测试结果：{'成功' if sendinput_result else '失败'}")
        print("\n请观察游戏是否有反应（按钮被点击等）")
        input("按 Enter 键继续...")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if args.test_method == 'both':
        if postmessage_result and sendinput_result:
            print("✓ 两种方法都成功")
            print("建议：优先使用 PostMessage 方法（不影响前台操作）")
        elif postmessage_result:
            print("✓ PostMessage 方法成功")
            print("建议：使用 PostMessage 方法")
        elif sendinput_result:
            print("✓ SendInput 方法成功")
            print("建议：游戏不支持 PostMessage，使用 SendInput 方法（鼠标瞬移）")
        else:
            print("✗ 两种方法都失败")
            print("建议：检查窗口句柄和坐标是否正确")
    elif args.test_method == 'postmessage':
        print(f"PostMessage 测试结果：{'成功' if postmessage_result else '失败'}")
        if postmessage_result:
            print("建议：游戏支持 PostMessage，可以使用后台消息模式")
        else:
            print("建议：游戏可能不支持 PostMessage，尝试 SendInput 方法")
    elif args.test_method == 'sendinput':
        print(f"SendInput 测试结果：{'成功' if sendinput_result else '失败'}")
        if sendinput_result:
            print("建议：游戏支持 SendInput，可以使用鼠标瞬移模式")
        else:
            print("建议：检查窗口句柄和坐标是否正确")

if __name__ == "__main__":
    main()
