# -*- coding: utf-8 -*-
"""
改进的按钮点击测试脚本
添加了更好的错误处理和调试信息
"""

import argparse
import sys
import os
import time
import win32gui
import traceback
from airtest.core.api import *
from airtest.core.settings import Settings as ST
from airtest.core.error import TargetNotFoundError

# 添加脚本管理器目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入后台设备类
from background_windows import BackgroundWindows

def main():
    parser = argparse.ArgumentParser(description='按钮点击测试脚本')
    parser.add_argument('--window-hwnd', type=int, help='窗口句柄')
    parser.add_argument('--window-title', type=str, help='窗口标题')
    parser.add_argument('--bg-mode', type=str, default='message', help='后台模式')
    parser.add_argument('--run-mode', type=str, default='background', help='运行模式')
    
    args = parser.parse_args()
    
    # 设置 Airtest 全局参数
    ST.THRESHOLD = 0.7
    ST.OPDELAY = 0.5
    ST.CVSTRATEGY = ["sift", "brisk"]
    
    print("=" * 60)
    print("按钮点击测试脚本")
    print("=" * 60)
    print(f"运行模式：{args.run_mode}")
    print(f"后台模式：{args.bg_mode}")
    
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
    
    # 测试获取屏幕截图
    print("\n测试获取屏幕截图...")
    try:
        print(f"调用 snapshot() 方法...")
        
        # 直接使用设备的 snapshot 方法
        screen = bg_dev.snapshot()
        
        print(f"snapshot() 返回类型：{type(screen)}")
        
        if screen is None:
            print("错误：截图失败，返回 None")
            return
        
        print(f"截图成功，大小：{screen.shape}")
        print("截图功能正常！")
    except Exception as e:
        print(f"截图失败：{e}")
        traceback.print_exc()
        return
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试查找按钮图片
    button_image = os.path.join(script_dir, "test_button.png")
    if os.path.exists(button_image):
        print(f"\n找到按钮图片：{button_image}")
        button_template = Template(button_image)
        
        # 尝试找到并点击按钮
        print("尝试查找按钮...")
        try:
            pos = wait(button_template, timeout=10)
            print(f"找到按钮，位置：{pos}")
            
            # 点击按钮
            print("点击按钮...")
            touch(pos)
            print("点击完成")
            
            # 等待一段时间
            time.sleep(2)
            
            # 再次截图验证
            print("\n验证点击结果...")
            screen2 = snapshot()
            if screen2 is not None:
                print(f"验证截图成功，大小：{screen2.shape}")
            else:
                print("验证截图失败")
                
        except TargetNotFoundError:
            print("错误：未找到按钮图片")
            print("可能原因：")
            print("  1. 按钮图片与实际按钮不匹配")
            print("  2. 窗口内容已改变")
            print("  3. 截图区域不正确")
        except Exception as e:
            print(f"点击失败：{e}")
            traceback.print_exc()
    else:
        print(f"\n错误：未找到按钮图片 {button_image}")
    
    print("\n测试完成")

if __name__ == "__main__":
    main()
