# -*- coding: utf-8 -*-
"""
使用图像识别的按钮点击测试脚本
"""

import sys
import os
import time
import win32gui
from airtest.core.api import *
from airtest.core.settings import Settings as ST
from airtest.aircv import imread

# 设置 Airtest 全局参数
ST.THRESHOLD = 0.7
ST.OPDELAY = 0.5
ST.CVSTRATEGY = ["sift", "brisk"]

print("=" * 60)
print("使用图像识别的按钮点击测试脚本")
print("=" * 60)

# 初始化 Windows 设备
print("\n初始化 Windows 设备...")
auto_setup(__file__, devices=["Windows:///"])
print(f"设备初始化成功，类型：{type(G.DEVICE)}")

# 查找测试窗口
print("\n查找测试窗口...")
hwnd = win32gui.FindWindow(None, "测试窗口")
if hwnd == 0:
    print("未找到测试窗口")
    sys.exit(1)

print(f"找到测试窗口，句柄：{hwnd}")

# 截图
print("\n截图...")
screenshot_path = "test_screenshot.png"
snapshot(filename=screenshot_path)
print(f"截图保存到：{screenshot_path}")

# 等待用户选择按钮位置
print("\n请打开 test_screenshot.png 文件")
print("然后手动点击测试按钮，观察点击次数是否增加")
print("\n输入 'yes' 继续，或 'quit' 退出：")
user_input = input().strip().lower()
if user_input == 'quit':
    sys.exit(0)

# 显示当前窗口信息
print(f"\n当前窗口信息：")
print(f"  句柄：{hwnd}")
print(f"  位置：{win32gui.GetWindowRect(hwnd)}")
print(f"  标题：{win32gui.GetWindowText(hwnd)}")

# 测试多次点击
print("\n" + "=" * 40)
print("开始多次点击测试")
print("=" * 40)

# 计算窗口中心位置
window_rect = win32gui.GetWindowRect(hwnd)
center_x = window_rect[0] + (window_rect[2] - window_rect[0]) // 2
center_y = window_rect[1] + (window_rect[3] - window_rect[1]) // 2

# 定义按钮区域（根据测试窗口的布局，按钮大概在窗口中心偏上位置）
button_x = center_x
button_y = center_y - 50

print(f"\n尝试点击坐标：({button_x}, {button_y})")

for i in range(3):
    print(f"\n点击 {i+1}/3")
    touch((button_x, button_y))
    time.sleep(1)

print("\n" + "=" * 40)
print("点击测试完成！")
print("请观察测试窗口中的'点击次数'是否增加")
print("=" * 40)
