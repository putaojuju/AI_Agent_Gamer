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
parser.add_argument('--run-mode', type=str, default='normal', help='运行模式')
args = parser.parse_args()

# 添加脚本管理器目录到Python路径，以便导入自定义类
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# 设置Airtest全局参数
ST.THRESHOLD = 0.7  # 降低识别阈值，提高识别成功率
ST.OPDELAY = 0.5    # 操作间隔延迟
ST.CVSTRATEGY = ["sift", "brisk"]  # 优先使用sift算法，后台模式不支持template

# 初始化Windows设备（关键：让Airtest能控制游戏窗口）
# 如果传入了窗口句柄，使用自定义的后台设备类（无论是否为后台模式）
if args.window_hwnd:
    try:
        print("使用后台消息模式，加载自定义设备类...")
        from background_windows import BackgroundWindows
        
        # 使用默认方式初始化设备
        auto_setup(__file__, devices=["Windows:///"])
        
        # 获取当前设备并替换为自定义设备
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
        print(f"运行模式：{args.run_mode}")
        print(f"后台模式：{args.bg_mode}")
        
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

# 窗口状态检测和处理
def check_window_state():
    """检查游戏窗口状态"""
    # 获取当前连接的设备
    dev = device()
    print(f"当前连接设备：{dev}")
    
    hwnd = None
    
    # 优先使用传入的窗口句柄
    if args.window_hwnd:
        hwnd = args.window_hwnd
        print(f"使用传入的窗口句柄：{hwnd}")
    elif args.window_title:
        # 如果没有传入句柄，才通过标题查找
        hwnd = win32gui.FindWindow(None, args.window_title)
        if hwnd == 0:
            print(f"未找到指定标题的窗口：{args.window_title}")
            return False
        print(f"找到指定窗口：{args.window_title} (句柄：{hwnd})")
    else:
        # 获取当前活跃窗口
        hwnd = win32gui.GetForegroundWindow()
        if hwnd == 0:
            print("未找到活跃窗口")
            return False
        # 获取窗口标题
        title = win32gui.GetWindowText(hwnd)
        print(f"当前活跃窗口：{title} (句柄：{hwnd})")
    
    # 检查窗口是否有效
    if not win32gui.IsWindow(hwnd):
        print(f"窗口句柄无效：{hwnd}")
        return False
    
    # 检查窗口是否可见（后台模式下窗口可能被移到屏幕外）
    is_visible = win32gui.IsWindowVisible(hwnd)
    print(f"窗口可见性：{is_visible}")
    
    # 后台模式下不需要调整窗口可见性和激活状态
    # 保持窗口当前状态，确保Airtest可以正常截图
    print("窗口状态正常，跳过可见性和最大化调整")
    
    return True

# 执行窗口状态检查
print("开始窗口状态检查...")
if not check_window_state():
    print("窗口状态检查失败，脚本可能无法正常执行")
else:
    print("窗口状态检查成功")

# ===============================================
# 自动化流程开始
# ===============================================

# 1. 触碰start.png
print("步骤1: 触碰start.png")
start_template = Template(r"start.png", threshold=0.7)
touch(start_template)

# 2. 等待coin.png出现，等待1s后触碰
print("步骤2: 等待coin.png出现")
coin_template = Template(r"coin.png", threshold=0.7)
wait(coin_template, timeout=10)
sleep(1)
touch(coin_template)

# 3. 等待all_skip.png出现，等待1s后触碰
print("步骤3: 等待all_skip.png出现")
# 使用简化的Template定义，添加置信度参数提高识别成功率
all_skip_template = Template(r"all_skip.png", threshold=0.7)
wait(all_skip_template, timeout=10)
sleep(1)
touch(all_skip_template)

# 4. 等待ok.png出现，等待1s后触碰
print("步骤4: 等待ok.png出现")
ok_template = Template(r"ok.png", threshold=0.7)
wait(ok_template, timeout=10)
sleep(1)
touch(ok_template)

# 5. 等待hai.png出现，等待1s后触碰
print("步骤5: 等待hai.png出现")
hai_template = Template(r"hai.png", threshold=0.7)
wait(hai_template, timeout=10)
sleep(1)
touch(hai_template)

# 6. 等待3s
print("步骤6: 等待3s")
sleep(3)

# 7. 鼠标左键点击
print("步骤7: 鼠标左键点击")
touch((-1, -1))  # 直接传入坐标元组，使用相对坐标(-1,-1)表示当前位置点击，或根据实际情况调整

# 8. 等待back.png出现，等待1s后触碰
print("步骤8: 等待back.png出现")
back_template = Template(r"back.png", threshold=0.7)
wait(back_template, timeout=10)
sleep(1)
touch(back_template)

# 9. 等待Battle_Exercise.png出现，等待1s后触碰
print("步骤9: 等待Battle_Exercise.png出现")
battle_template = Template(r"Battle_Exercise.png", threshold=0.7)
wait(battle_template, timeout=10)
sleep(1)
touch(battle_template)

# 10. 等待fire.png出现，1s之后按平均概率随机选择元素触碰
print("步骤10: 等待fire.png出现")
fire_template = Template(r"fire.png", threshold=0.7)
wait(fire_template, timeout=10)
sleep(1)

# 随机选择元素
print("步骤10: 随机选择元素触碰")
elements = [
    Template(r"fire.png", threshold=0.7),
    Template(r"wate.png", threshold=0.7),  # 修正文件名：wate.png（缺少r字母）
    Template(r"thunder.png", threshold=0.7),
    Template(r"radiance.png", threshold=0.7),
    Template(r"dark.png", threshold=0.7)
]

# 随机选择一个元素
selected_element = random.choice(elements)
touch(selected_element)
print(f"已选择触碰: {selected_element.filename}")

# 11. 等待back.png出现，1s后触碰
print("步骤11: 等待back.png出现")
wait(back_template, timeout=10)
sleep(1)
touch(back_template)

# ===============================================
# 自动化流程结束
# ===============================================

# 脚本执行完成的标记
print("脚本执行完成")









