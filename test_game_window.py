# -*- coding: utf-8 -*-
"""
测试脚本：验证GameWindow类的修复效果
用于测试游戏窗口截图修复，检查是否能找到渲染子窗口并成功截图
"""

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game_window import GameWindow

def main():
    print("=" * 60)
    print("GameWindow修复测试脚本")
    print("=" * 60)
    print()
    
    # 初始化GameWindow实例
    game_window = GameWindow()
    
    # 列出所有可见窗口
    print("1. 列出所有可见窗口：")
    windows = game_window.get_all_windows()
    
    if not windows:
        print("   未找到可见窗口")
        return
    
    for i, (hwnd, title) in enumerate(windows[:10], 1):
        print(f"   [{i:2d}] HWND: {hwnd:10d} | Title: {title}")
    
    if len(windows) > 10:
        print(f"   ... 还有 {len(windows) - 10} 个窗口")
    
    print()
    # 让用户选择一个窗口
    try:
        choice = input("2. 请输入要测试的窗口编号 (1-10): ")
        choice = int(choice)
        if choice < 1 or choice > min(10, len(windows)):
            print("   无效的选择")
            return
        
        target_hwnd, target_title = windows[choice - 1]
        print(f"   选择的窗口：{target_title} (HWND: {target_hwnd})")
    except ValueError:
        print("   无效的输入")
        return
    
    print()
    # 初始化窗口句柄
    print("3. 初始化窗口句柄：")
    success = game_window.init_hwnd(target_hwnd)
    
    if success:
        print(f"   ✓ 窗口初始化成功")
        print(f"   窗口标题：{game_window.window_title}")
        print(f"   主窗口句柄：{game_window.hwnd}")
        print(f"   渲染子窗口句柄：{game_window.render_hwnd}")
        print(f"   窗口大小：{game_window.width}x{game_window.height}")
    else:
        print("   ✗ 窗口初始化失败")
        return
    
    print()
    # 测试截图功能
    print("4. 测试截图功能：")
    for i in range(3):
        print(f"   尝试截图 {i+1}/3...")
        screenshot = game_window.snapshot()
        
        if screenshot is not None:
            print(f"   ✓ 截图成功，大小：{screenshot.shape}")
            # 检查是否是RGB图像
            if len(screenshot.shape) == 3 and screenshot.shape[2] == 3:
                print("   ✓ 截图格式正确 (RGB)")
            else:
                print("   ⚠ 截图格式可能有问题")
            break
        else:
            print("   ✗ 截图失败")
            time.sleep(1)
    
    if screenshot is None:
        print("   截图测试失败")
        return
    
    print()
    # 总结测试结果
    print("5. 测试总结：")
    print("   " + "=" * 40)
    
    if game_window.render_hwnd:
        print("   ✓ 成功找到渲染子窗口")
        print(f"   渲染子窗口句柄：{game_window.render_hwnd}")
    else:
        print("   ⚠ 未找到渲染子窗口，使用主窗口")
    
    print("   ✓ 窗口初始化成功")
    print("   ✓ 截图功能正常")
    print("   " + "=" * 40)
    print("   测试完成！")

if __name__ == "__main__":
    main()