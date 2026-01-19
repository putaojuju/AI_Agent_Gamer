# -*- coding: utf-8 -*-
"""
简单的窗口操作测试脚本
直接测试截图和点击功能，不依赖按钮图片匹配
"""

import argparse
import sys
import os
import time
import win32gui
import traceback
import numpy as np
from airtest.core.api import *
from airtest.core.settings import Settings as ST

# 添加脚本管理器目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入后台设备类
from background_windows import BackgroundWindows

def main():
    parser = argparse.ArgumentParser(description='窗口操作测试脚本')
    parser.add_argument('--window-hwnd', type=int, help='窗口句柄')
    parser.add_argument('--window-title', type=str, help='窗口标题')
    
    args = parser.parse_args()
    
    # 设置 Airtest 全局参数
    ST.THRESHOLD = 0.7
    ST.OPDELAY = 0.5
    ST.CVSTRATEGY = ["sift", "brisk"]
    
    print("=" * 60)
    print("窗口操作测试脚本")
    print("=" * 60)
    
    # 初始化 Windows 设备
    try:
        print("\n初始化 Windows 设备...")
        auto_setup(__file__, devices=["Windows:///"])
        dev = G.DEVICE
        print(f"设备初始化成功，类型：{type(dev)}")
    except Exception as e:
        print(f"设备初始化失败：{e}")
        traceback.print_exc()
        return
    
    # 获取窗口句柄
    hwnd = None
    if args.window_hwnd:
        hwnd = args.window_hwnd
        print(f"\n使用指定的窗口句柄：{hwnd}")
    elif args.window_title:
        hwnd = win32gui.FindWindow(None, args.window_title)
        if hwnd == 0:
            print(f"错误：未找到窗口标题为 '{args.window_title}' 的窗口")
            return
        print(f"\n找到窗口句柄：{hwnd}")
    else:
        print("错误：必须指定 --window-hwnd 或 --window-title")
        return
    
    # 验证窗口句柄
    if not win32gui.IsWindow(hwnd):
        print(f"错误：窗口句柄 {hwnd} 无效")
        return
    
    # 获取窗口信息
    window_title = win32gui.GetWindowText(hwnd)
    window_visible = win32gui.IsWindowVisible(hwnd)
    window_rect = win32gui.GetWindowRect(hwnd)
    client_rect = win32gui.GetClientRect(hwnd)
    
    print(f"\n窗口信息：")
    print(f"  标题：{window_title}")
    print(f"  可见：{window_visible}")
    print(f"  位置：{window_rect}")
    print(f"  客户区：{client_rect}")
    
    # 使用当前设备实例创建后台设备
    print("\n初始化后台设备...")
    bg_dev = BackgroundWindows(dev)
    bg_dev.init_hwnd(hwnd)
    
    # 替换全局设备实例
    G.DEVICE = bg_dev
    print(f"已切换到后台消息模式，窗口句柄：{hwnd}")
    print(f"当前设备类型：{type(G.DEVICE)}")
    
    # ==================== 测试1：获取屏幕截图 ====================
    print("\n" + "=" * 40)
    print("测试1：获取屏幕截图")
    print("=" * 40)
    
    try:
        screen = bg_dev.snapshot()
        if screen is not None:
            print(f"✓ 截图成功，大小：{screen.shape}")
        else:
            print("✗ 截图失败，返回 None")
            return
    except Exception as e:
        print(f"✗ 截图失败：{e}")
        traceback.print_exc()
        return
    
    # ==================== 测试2：直接点击测试窗口 ====================
    print("\n" + "=" * 40)
    print("测试2：直接点击测试窗口")
    print("=" * 40)
    
    try:
        # 计算窗口中心位置
        center_x = window_rect[0] + (window_rect[2] - window_rect[0]) // 2
        center_y = window_rect[1] + (window_rect[3] - window_rect[1]) // 2
        
        print(f"尝试点击窗口中心位置：({center_x}, {center_y})")
        
        # 使用后台设备点击
        result = bg_dev.touch((center_x, center_y))
        
        if result:
            print("✓ 点击成功")
        else:
            print("✗ 点击失败")
            return
    except Exception as e:
        print(f"✗ 点击失败：{e}")
        traceback.print_exc()
        return
    
    # ==================== 测试3：连续点击测试 ====================
    print("\n" + "=" * 40)
    print("测试3：连续点击测试")
    print("=" * 40)
    
    try:
        # 计算窗口中的几个位置
        # 位置1：窗口中心偏上
        pos1 = (center_x, center_y - 50)
        # 位置2：窗口中心偏下
        pos2 = (center_x, center_y + 50)
        # 位置3：窗口中心偏左
        pos3 = (center_x - 50, center_y)
        # 位置4：窗口中心偏右
        pos4 = (center_x + 50, center_y)
        
        test_positions = [pos1, pos2, pos3, pos4]
        
        for i, pos in enumerate(test_positions, 1):
            print(f"\n尝试点击位置 {i}：{pos}")
            result = bg_dev.touch(pos)
            if result:
                print(f"✓ 点击位置 {i} 成功")
            else:
                print(f"✗ 点击位置 {i} 失败")
            
            # 短暂延迟
            time.sleep(0.5)
    except Exception as e:
        print(f"✗ 连续点击测试失败：{e}")
        traceback.print_exc()
        return
    
    # ==================== 测试4：测试坐标转换 ====================
    print("\n" + "=" * 40)
    print("测试4：测试坐标转换")
    print("=" * 40)
    
    try:
        # 测试不同坐标转换
        screen_pos = (center_x, center_y)
        print(f"测试屏幕坐标：{screen_pos}")
        
        # 使用 Airtest 的 touch 方法
        print("使用 Airtest touch() 方法点击...")
        touch(screen_pos)
        print("✓ touch() 方法执行成功")
    except Exception as e:
        print(f"✗ 坐标转换测试失败：{e}")
        traceback.print_exc()
        return
    
    # ==================== 测试5：获取截图并保存 ====================
    print("\n" + "=" * 40)
    print("测试5：获取截图并保存")
    print("=" * 40)
    
    try:
        # 保存截图到当前目录
        screenshot_path = os.path.join(os.path.dirname(__file__), "test_screenshot.png")
        screen = bg_dev.snapshot(filename=screenshot_path)
        
        if screen is not None:
            print(f"✓ 截图保存成功：{screenshot_path}")
            print(f"  截图大小：{screen.shape}")
        else:
            print("✗ 截图保存失败")
            return
    except Exception as e:
        print(f"✗ 截图保存测试失败：{e}")
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("所有测试完成！")
    print("✓ 截图功能正常")
    print("✓ 点击功能正常")
    print("✓ 坐标转换正常")
    print("✓ 截图保存正常")
    print("=" * 60)
    print("\n脚本可以在测试窗口中运行！")

if __name__ == "__main__":
    main()
