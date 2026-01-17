# -*- coding: utf-8 -*-
"""
游戏鼠标点击拦截测试脚本 - 双方法对比
同时测试PostMessage和SendInput两种点击方法，用于比较游戏拦截情况
"""

import time
import random
import sys
import os
from airtest.core.api import *
from airtest.core.settings import Settings as ST

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入后台设备类
try:
    from background_windows import BackgroundWindows
    HAS_BACKGROUND_MODULE = True
    print("✓ 成功导入后台设备模块")
except ImportError as e:
    HAS_BACKGROUND_MODULE = False
    print(f"✗ 导入后台设备模块失败: {e}")

# 设置Airtest全局参数
ST.THRESHOLD = 0.7
ST.OPDELAY = 0.5
ST.CVSTRATEGY = ["sift", "brisk"]

# 设置预定义的点击位置（屏幕坐标）
# 这些位置覆盖屏幕的主要区域，确保能点击到游戏窗口
CLICK_POSITIONS = [
    (960, 540),    # 屏幕中心
    (480, 270),    # 左上区域
    (1440, 270),   # 右上区域
    (480, 810),    # 左下区域
    (1440, 810),   # 右下区域
    (960, 270),    # 上中区域
    (960, 810),    # 下中区域
    (640, 540),    # 左中区域
    (1280, 540),   # 右中区域
]

def test_sendinput_click(x, y):
    """
    使用SendInput方法点击
    """
    try:
        touch((x, y))
        return True, "SendInput方法"
    except Exception as e:
        return False, f"SendInput方法失败: {e}"

def test_postmessage_click(x, y):
    """
    使用PostMessage方法点击
    """
    if not HAS_BACKGROUND_MODULE:
        return False, "PostMessage模块未导入"
    
    try:
        # 获取当前设备
        dev = G.DEVICE
        
        # 如果当前设备不是BackgroundWindows，创建一个临时的
        if not isinstance(dev, BackgroundWindows):
            bg_dev = BackgroundWindows(dev)
            # 直接使用屏幕坐标点击
            bg_dev._send_click_message((x, y))
        else:
            # 已经是BackgroundWindows设备，直接使用
            dev._send_click_message((x, y))
        
        return True, "PostMessage方法"
    except Exception as e:
        return False, f"PostMessage方法失败: {e}"

def main():
    print("=" * 60)
    print("游戏鼠标点击拦截测试脚本 - 双方法对比")
    print("=" * 60)
    print("\n使用说明：")
    print("1. 请先打开游戏窗口并最大化")
    print("2. 确保游戏窗口覆盖整个屏幕")
    print("3. 观察游戏中的点击特效或反馈")
    print("4. 如果看到点击特效，说明点击成功")
    print("5. 如果没有点击特效，说明游戏可能拦截了点击")
    print("\n测试开始后，只在屏幕正中央(960, 540)循环点击：")
    print("  - PostMessage方法（基于窗口消息，不影响前台）")
    print("  - SendInput方法（鼠标瞬移，模拟真实鼠标移动）")
    print("\n两种方法交替使用，每次点击间隔3秒")
    print("\n按 Ctrl+C 可以停止测试")
    print("=" * 60)
    
    # 初始化Airtest设备
    print("\n正在初始化Airtest设备...")
    try:
        auto_setup(__file__, devices=["Windows:///"])
        print("✓ Airtest设备初始化成功")
    except Exception as e:
        print(f"✗ Airtest设备初始化失败: {e}")
        return
    
    # 等待用户准备
    input("\n按 Enter 键开始测试...")
    
    print("\n测试开始！")
    print("点击位置序列：")
    
    test_count = 0
    center_x, center_y = 960, 540  # 屏幕正中央坐标
    
    try:
        while True:
            test_count += 1
            
            print(f"\n[测试 #{test_count}] 位置: ({center_x}, {center_y}) - 屏幕正中央")
            print(f"  时间: {time.strftime('%H:%M:%S')}")
            
            # 循环使用两种方法
            if test_count % 2 == 1:
                # 奇数次测试：PostMessage方法
                print("  \n方法: PostMessage（窗口消息）")
                success, result = test_postmessage_click(center_x, center_y)
                method_name = "PostMessage"
            else:
                # 偶数次测试：SendInput方法
                print("  \n方法: SendInput（鼠标瞬移）")
                success, result = test_sendinput_click(center_x, center_y)
                method_name = "SendInput"
            
            if success:
                print(f"    ✓ {method_name}方法点击成功")
            else:
                print(f"    ✗ {result}")
            
            # 等待3秒，准备下一次测试
            print(f"  等待3秒，准备使用另一种方法...")
            time.sleep(3)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("测试已停止")
        print("=" * 60)
        print(f"\n总点击次数: {click_count}")
        print(f"  每次点击测试2种方法，共测试: {click_count * 2}次")
        print("\n测试结果分析：")
        print("1. 如果在游戏中看到了点击特效，说明该方法有效")
        print("2. 如果没有点击特效，说明游戏可能拦截了该方法")
        print("3. 请对比两种方法的效果：")
        print("   - 如果SendInput有效而PostMessage无效：游戏拦截了窗口消息")
        print("   - 如果PostMessage有效而SendInput无效：很少见，可能是设备问题")
        print("   - 如果两种方法都有效：游戏未拦截点击")
        print("   - 如果两种方法都无效：可能是坐标问题或游戏防护机制很强")
        print("\n建议：")
        print("- 尝试不同的点击位置")
        print("- 调整点击频率")
        print("- 检查游戏是否有防护机制")
        print("=" * 60)

if __name__ == "__main__":
    main()
