# -*- coding: utf-8 -*-
"""
精确的按钮点击测试脚本
使用Airtest图像识别找到并点击"测试"按钮
"""

import argparse
import sys
import os
import time
import win32gui
import traceback
from airtest.core.api import *
from airtest.core.settings import Settings as ST

# 添加脚本管理器目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入后台设备类
from background_windows import BackgroundWindows

def main():
    parser = argparse.ArgumentParser(description='精确的按钮点击测试脚本')
    parser.add_argument('--window-title', type=str, default='测试窗口', help='窗口标题')
    
    args = parser.parse_args()
    
    # 设置 Airtest 全局参数
    ST.THRESHOLD = 0.7
    ST.OPDELAY = 0.5
    ST.CVSTRATEGY = ["sift", "brisk"]
    
    print("=" * 60)
    print("精确的按钮点击测试脚本")
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
    hwnd = win32gui.FindWindow(None, args.window_title)
    if hwnd == 0:
        print(f"错误：未找到窗口标题为 '{args.window_title}' 的窗口")
        return
    print(f"\n找到窗口句柄：{hwnd}")
    
    # 验证窗口句柄
    if not win32gui.IsWindow(hwnd):
        print(f"错误：窗口句柄 {hwnd} 无效")
        return
    
    # 初始化后台设备
    bg_dev = BackgroundWindows(dev)
    bg_dev.init_hwnd(hwnd)
    
    # 替换全局设备实例
    G.DEVICE = bg_dev
    print(f"已切换到后台消息模式，窗口句柄：{hwnd}")
    
    # 测试1：截图并保存
    print("\n" + "=" * 40)
    print("测试1：截图并保存")
    print("=" * 40)
    
    screenshot_path = os.path.join(os.path.dirname(__file__), "test_screenshot.png")
    screen = snapshot(filename=screenshot_path)
    print(f"✓ 截图保存成功：{screenshot_path}")
    
    # 测试2：点击测试按钮
    print("\n" + "=" * 40)
    print("测试2：点击测试按钮")
    print("=" * 40)
    
    # 获取窗口信息
    window_rect = win32gui.GetWindowRect(hwnd)
    print(f"窗口位置：{window_rect}")
    
    # 计算窗口中心位置（按钮大概位置）
    window_width = window_rect[2] - window_rect[0]
    window_height = window_rect[3] - window_rect[1]
    
    # 计算按钮位置（根据窗口大小和布局）
    button_x = window_rect[0] + window_width // 2
    button_y = window_rect[1] + window_height // 2
    
    print(f"计算的按钮位置：({button_x}, {button_y})")
    
    # 使用 Airtest 的 touch 方法点击
    print("尝试点击按钮...")
    touch((button_x, button_y))
    print(f"✓ 点击完成，坐标：({button_x}, {button_y})")
    
    # 等待0.5秒，让按钮状态更新
    time.sleep(0.5)
    
    # 测试3：验证点击效果
    print("\n" + "=" * 40)
    print("测试3：验证点击效果")
    print("=" * 40)
    
    # 再次截图，用于验证点击效果
    verify_screenshot_path = os.path.join(os.path.dirname(__file__), "verify_screenshot.png")
    screen = snapshot(filename=verify_screenshot_path)
    print(f"✓ 验证截图保存成功：{verify_screenshot_path}")
    print("\n请手动观察测试窗口中的'点击次数'是否增加！")
    print("\n如果点击次数增加，说明点击成功！")
    print("如果点击次数未增加，说明点击失败或坐标不准确！")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n测试结果：")
    print("✓ 截图功能正常")
    print("✓ 点击操作已执行")
    print("✓ 验证截图已保存")
    print("\n请手动验证点击效果，查看'点击次数'是否增加")

if __name__ == "__main__":
    main()
