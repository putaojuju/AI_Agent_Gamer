# -*- coding: utf-8 -*-
"""
自动测试脚本：验证GameWindow修复效果
无需用户交互，自动测试窗口初始化和截图功能
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_window import GameWindow

def test_game_window():
    print("=" * 60)
    print("GameWindow自动测试脚本")
    print("=" * 60)
    print()
    
    # 初始化GameWindow实例
    game_window = GameWindow()
    
    # 列出所有可见窗口
    print("1. 列出所有可见窗口：")
    windows = game_window.get_all_windows()
    
    if not windows:
        print("   未找到可见窗口")
        return False
    
    # 只测试前5个窗口
    test_windows = windows[:5]
    
    for i, (hwnd, title) in enumerate(test_windows, 1):
        print(f"   [{i:2d}] HWND: {hwnd:10d} | Title: {title}")
    
    print()
    
    # 测试每个窗口
    success_count = 0
    total_count = len(test_windows)
    
    for i, (hwnd, title) in enumerate(test_windows, 1):
        print(f"2. 测试窗口 {i}/{total_count}：")
        print(f"   窗口标题：{title}")
        print(f"   窗口句柄：{hwnd}")
        
        # 初始化窗口句柄
        print("   初始化窗口...")
        success = game_window.init_hwnd(hwnd)
        
        if success:
            print(f"   ✓ 窗口初始化成功")
            print(f"   主窗口句柄：{game_window.hwnd}")
            print(f"   渲染子窗口句柄：{game_window.render_hwnd}")
            print(f"   窗口大小：{game_window.width}x{game_window.height}")
            
            # 测试截图功能
            print("   测试截图...")
            screenshot = game_window.snapshot()
            
            if screenshot is not None:
                print(f"   ✓ 截图成功，大小：{screenshot.shape}")
                # 检查是否是RGB图像
                if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
                    print("   ✓ 截图格式正确 (RGB)")
                else:
                    print("   ⚠ 截图格式可能有问题")
                success_count += 1
            else:
                print("   ✗ 截图失败")
        else:
            print("   ✗ 窗口初始化失败")
        
        print()
    
    print("3. 测试总结：")
    print("   " + "=" * 40)
    print(f"   测试窗口数：{total_count}")
    print(f"   成功窗口数：{success_count}")
    print(f"   成功率：{(success_count / total_count) * 100:.1f}%")
    print("   " + "=" * 40)
    
    if success_count > 0:
        print("   ✓ 修复测试通过！")
        return True
    else:
        print("   ✗ 修复测试失败！")
        return False

if __name__ == "__main__":
    test_game_window()