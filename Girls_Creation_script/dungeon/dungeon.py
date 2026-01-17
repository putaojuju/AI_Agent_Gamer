# -*- coding: utf-8 -*-
__author__ = "TraeAI"

# 导入Airtest核心库和random模块
from airtest.core.api import *
from airtest.core.settings import Settings as ST
import random
import win32gui
import win32con
import time
import sys
import os
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description='Airtest游戏脚本')
parser.add_argument('--window-title', type=str, help='游戏窗口标题')
parser.add_argument('--window-hwnd', type=int, help='游戏窗口句柄')
parser.add_argument('--bg-mode', type=str, default='message', help='后台运行模式')
args = parser.parse_args()

# 添加脚本管理器目录到Python路径，以便导入自定义类
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 设置Airtest全局参数
ST.THRESHOLD = 0.7  # 降低识别阈值，提高识别成功率
ST.OPDELAY = 0.5    # 操作间隔延迟

# 初始化Windows设备（关键：让Airtest能控制游戏窗口）
# 如果传入了窗口句柄和后台模式，使用自定义的后台设备类
if args.window_hwnd and args.bg_mode == 'message':
    try:
        print("使用后台消息模式，加载自定义设备类...")
        from background_windows import BackgroundWindows
        
        # 使用默认方式初始化设备
        auto_setup(__file__, devices=["Windows:///"])
        
        # 获取当前设备
        dev = device()
        print(f"原始设备：{dev}")
        
        # 直接替换全局设备实例
        import airtest.core.api as api
        # 使用当前设备实例创建后台设备
        bg_dev = BackgroundWindows(dev)  # dev是已经初始化的设备
        bg_dev.init_hwnd(args.window_hwnd)
        
        # 替换全局设备实例
        api.G.DEVICE = bg_dev
        print(f"已切换到后台消息模式，窗口句柄：{args.window_hwnd}")
        print(f"当前设备类型：{type(api.G.DEVICE)}")
        
    except Exception as e:
        print(f"加载后台消息模式失败：{e}")
        print("降级为默认连接方式...")
        # 降级为默认连接方式
        if args.window_title:
            device_str = f"Windows:///?title={args.window_title}"
            print(f"使用指定窗口标题连接：{device_str}")
            auto_setup(__file__, devices=[device_str])
        else:
            print("使用默认方式连接（当前前台窗口）")
            auto_setup(__file__, devices=["Windows:///"])

elif args.window_title:
    # 使用指定窗口标题连接
    device_str = f"Windows:///?title={args.window_title}"
    print(f"使用指定窗口标题连接：{device_str}")
    auto_setup(__file__, devices=[device_str])
else:
    # 留空表示连接当前前台的Windows窗口
    print("使用默认方式连接（当前前台窗口）")
    auto_setup(__file__, devices=["Windows:///"])

touch(Template(r"tpl1768228936964.png", record_pos=(0.187, 0.234), resolution=(1271, 720)))
sleep(3)
touch(Template(r"tpl1768228941568.png", record_pos=(0.332, 0.194), resolution=(1271, 720)))
sleep(3)
touch(Template(r"tpl1768233258765.png", record_pos=(0.263, 0.225), resolution=(1271, 720)))
sleep(3)
touch(Template(r"tpl1768228957935.png", record_pos=(0.314, -0.077), resolution=(1271, 720)))
sleep(3)
# 以下是空白区域，Airtest录制的操作会自动生成在这行之后
# 你只需点击IDE的“录制”按钮，操作游戏，代码会自动填充到这里

touch(Template(r"tpl1768233203389.png", record_pos=(0.221, 0.191), resolution=(1271, 720)))
touch(Template(r"tpl1768233213355.png", record_pos=(0.446, 0.198), resolution=(1271, 720)))
touch(Template(r"tpl1768233258765.png", record_pos=(0.263, 0.225), resolution=(1271, 720)))
touch(Template(r"tpl1768316752354.png", record_pos=(0.231, -0.148), resolution=(1280, 720)))

