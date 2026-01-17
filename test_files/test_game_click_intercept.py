# -*- coding: utf-8 -*-
"""
游戏鼠标点击拦截测试脚本
每隔2秒点击屏幕的一个随机位置，用于测试游戏是否会拦截鼠标点击信息
"""

import time
import random
import os
from airtest.core.api import *
from airtest.core.settings import Settings as ST

# 设置Airtest全局参数
ST.THRESHOLD = 0.7
ST.OPDELAY = 0.5

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

def main():
    print("=" * 60)
    print("游戏鼠标点击拦截测试脚本")
    print("=" * 60)
    print("\n使用说明：")
    print("1. 请先打开游戏窗口并最大化")
    print("2. 确保游戏窗口覆盖整个屏幕")
    print("3. 观察游戏中的点击特效或反馈")
    print("4. 如果看到点击特效，说明点击成功")
    print("5. 如果没有点击特效，说明游戏可能拦截了点击")
    print("\n测试开始后，每隔2秒会点击一个随机位置")
    print("按 Ctrl+C 可以停止测试")
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
    
    click_count = 0
    position_index = 0
    
    try:
        while True:
            # 获取点击位置
            if position_index < len(CLICK_POSITIONS):
                # 使用预定义的位置
                x, y = CLICK_POSITIONS[position_index]
                position_index += 1
            else:
                # 使用随机位置
                x = random.randint(100, 1820)
                y = random.randint(100, 980)
            
            click_count += 1
            
            # 执行点击
            print(f"\n[点击 #{click_count}] 位置: ({x}, {y})")
            print(f"  时间: {time.strftime('%H:%M:%S')}")
            
            try:
                touch((x, y))
                print(f"  ✓ 点击成功")
            except Exception as e:
                print(f"  ✗ 点击失败: {e}")
            
            # 等待2秒
            print(f"  等待2秒...")
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("测试已停止")
        print("=" * 60)
        print(f"\n总点击次数: {click_count}")
        print("\n测试结果分析：")
        print("1. 如果在游戏中看到了点击特效，说明点击成功")
        print("2. 如果没有看到点击特效，说明游戏可能拦截了点击")
        print("3. 建议尝试不同的点击位置和频率")
        print("=" * 60)

if __name__ == "__main__":
    main()
