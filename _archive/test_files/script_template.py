# -*- coding: utf-8 -*-
__author__ = "TraeAI"

import airtest.core.api as api
from airtest.core.settings import Settings as ST
import random
import win32gui
import win32con
import time
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='Airtest游戏脚本')
parser.add_argument('--window-title', type=str, help='游戏窗口标题')
parser.add_argument('--window-hwnd', type=int, help='游戏窗口句柄')
parser.add_argument('--bg-mode', type=str, default='message', help='后台运行模式')
parser.add_argument('--run-mode', type=str, default='normal', help='运行模式')
args = parser.parse_args()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

ST.THRESHOLD = 0.7
ST.OPDELAY = 0.5
ST.CVSTRATEGY = ["sift", "brisk"]

if args.window_hwnd:
    try:
        print("使用后台消息模式，加载自定义设备类...")
        from background_windows import BackgroundWindows
        
        api.auto_setup(__file__, devices=["Windows:///"])
        
        dev = api.device()
        print(f"原始设备：{dev}")
        
        bg_dev = BackgroundWindows(dev)
        bg_dev.init_hwnd(args.window_hwnd)
        
        api.G.DEVICE = bg_dev
        print(f"已切换到后台消息模式，窗口句柄：{args.window_hwnd}")
        print(f"当前设备类型：{type(api.G.DEVICE)}")
        print(f"运行模式：{args.run_mode}")
        print(f"后台模式：{args.bg_mode}")
        
    except Exception as e:
        print(f"加载后台消息模式失败：{e}")
        print("降级为默认连接方式...")
        if args.window_title:
            device_str = f"Windows:///?title={args.window_title}"
            print(f"使用指定窗口标题连接：{device_str}")
            api.auto_setup(__file__, devices=[device_str])
        else:
            print("使用默认方式连接（当前前台窗口）")
            api.auto_setup(__file__, devices=["Windows:///"])

elif args.window_title:
    device_str = f"Windows:///?title={args.window_title}"
    print(f"使用指定窗口标题连接：{device_str}")
    api.auto_setup(__file__, devices=[device_str])
else:
    print("使用默认方式连接（当前前台窗口）")
    api.auto_setup(__file__, devices=["Windows:///"])

def check_window_state():
    """检查游戏窗口状态"""
    dev = api.device()
    print(f"当前连接设备：{dev}")
    
    hwnd = None
    
    if args.window_hwnd:
        hwnd = args.window_hwnd
        print(f"使用传入的窗口句柄：{hwnd}")
    elif args.window_title:
        hwnd = win32gui.FindWindow(None, args.window_title)
        if hwnd == 0:
            print(f"未找到指定标题的窗口：{args.window_title}")
            return False
        print(f"找到指定窗口：{args.window_title} (句柄：{hwnd})")
    else:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            print("未找到活跃窗口")
            return False
        title = win32gui.GetWindowText(hwnd)
        print(f"当前活跃窗口：{title} (句柄：{hwnd})")
    
    if not win32gui.IsWindow(hwnd):
        print(f"窗口句柄无效：{hwnd}")
        return False
    
    is_visible = win32gui.IsWindowVisible(hwnd)
    print(f"窗口可见性：{is_visible}")
    
    print("窗口状态正常，跳过可见性和最大化调整")
    
    return True

print("开始窗口状态检查...")
if not check_window_state():
    print("窗口状态检查失败，脚本可能无法正常执行")
else:
    print("窗口状态检查成功")

api.touch(api.Template(r"example.png", threshold=0.7))
api.sleep(1)

print("脚本执行完成")
