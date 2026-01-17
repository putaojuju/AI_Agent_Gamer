# -*- coding: utf-8 -*-
"""
直接测试PostMessage点击的脚本
"""

import win32gui
import win32con
import time

# 查找测试窗口
hwnd = win32gui.FindWindow(None, "测试窗口")
if hwnd == 0:
    print("未找到测试窗口")
    exit(1)

print(f"找到测试窗口，句柄：{hwnd}")
print(f"窗口位置：{win32gui.GetWindowRect(hwnd)}")
print(f"窗口标题：{win32gui.GetWindowText(hwnd)}")

# 直接发送WM_LBUTTONDOWN和WM_LBUTTONUP消息
print("\n直接发送WM_LBUTTONDOWN和WM_LBUTTONUP消息...")

# 计算客户区中心位置（按钮大概位置）
window_rect = win32gui.GetWindowRect(hwnd)
width = window_rect[2] - window_rect[0]
height = window_rect[3] - window_rect[1]

# 客户区坐标（相对于窗口左上角）
client_x = width // 2
client_y = height // 2

print(f"窗口尺寸：{width}x{height}")
print(f"计算的客户区点击位置：({client_x}, {client_y})")

# 转换为lParam
l_param = (client_y << 16) | client_x
print(f"lParam：{l_param}")

# 发送鼠标按下消息
print(f"发送WM_LBUTTONDOWN消息到窗口 {hwnd}")
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
time.sleep(0.1)

# 发送鼠标释放消息
print(f"发送WM_LBUTTONUP消息到窗口 {hwnd}")
win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
time.sleep(0.1)

print("\n消息发送完成！")
print("请观察测试窗口中的'点击次数'是否增加")
print("\n注意：")
print("- 如果点击次数增加，说明PostMessage有效")
print("- 如果点击次数未增加，说明PostMessage无效或坐标错误")

# 尝试不同的坐标
print("\n" + "=" * 50)
print("尝试不同的坐标...")
print("=" * 50)

# 尝试多个可能的按钮位置
possible_positions = [
    (width // 2, height // 2 - 50),  # 中心偏上
    (width // 2, height // 2 - 40),  # 中心偏上
    (width // 2, height // 2 - 30),  # 中心偏上
    (width // 2, height // 2 - 20),  # 中心偏上
    (width // 2, height // 2 - 10),  # 中心偏上
    (width // 2, height // 2),        # 中心
]

for i, (x, y) in enumerate(possible_positions):
    print(f"\n尝试位置 {i+1}: ({x}, {y})")
    l_param = (y << 16) | x
    
    # 发送点击消息
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
    time.sleep(0.05)
    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
    time.sleep(0.1)

print("\n" + "=" * 50)
print("所有测试完成！")
print("=" * 50)
print("请观察测试窗口中的'点击次数'是否增加")
print("\n总结：")
print("1. 如果点击次数增加，说明游戏/窗口支持PostMessage")
print("2. 如果点击次数未增加，说明游戏/窗口可能拦截了PostMessage")
print("3. 建议使用SendInput（鼠标瞬移）方式")
