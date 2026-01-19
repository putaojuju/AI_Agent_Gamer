# -*- coding: utf-8 -*-
"""
独立测试脚本：测试游戏能否接收PostMessage
- 增加倒计时，确保能锁定到游戏窗口
- 开启后3秒发送一次SendInput
- 之后每隔3秒发送一次PostMessage
- 发送5次PostMessage后结束
"""
import sys
import os
import time
import io
import win32gui
import win32api

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from airtest.core.win.win import Windows
from background_windows import BackgroundWindows

def main():
    print("=" * 60)
    print("PostMessage 独立测试脚本 (修正版)")
    print("=" * 60)
    
    try:
        print("\n[1/3] 初始化 Windows 设备...")
        device = Windows()
        print("[SUCCESS] Windows 设备初始化成功")
        
        print("\n[2/3] 查找目标窗口...")
        print(">>> ⚠️ 请注意 ⚠️ <<<")
        print(">>> 请在 5 秒内点击/激活你的游戏窗口！！！ <<<")
        
        for i in range(5, 0, -1):
            print(f"倒计时: {i}...")
            time.sleep(1)
            
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            print("[ERROR] 未找到活动窗口")
            return False
        
        window_title = win32gui.GetWindowText(hwnd)
        print(f"\n[SUCCESS] 锁定窗口: [{window_title}]")
        print(f"[SUCCESS] 窗口句柄: {hwnd}")
        
        print("\n[3/3] 初始化后台模式...")
        bg_device = BackgroundWindows(device)
        bg_device.init_hwnd(hwnd)
        print("[SUCCESS] 后台模式初始化成功")
        
        window_rect = win32gui.GetWindowRect(hwnd)
        width = window_rect[2] - window_rect[0]
        height = window_rect[3] - window_rect[1]
        center_x = window_rect[0] + width // 2
        center_y = window_rect[1] + height // 2
        print(f"\n窗口尺寸: {width}x{height}")
        print(f"窗口中心坐标: ({center_x}, {center_y})")
        
        print("\n" + "=" * 60)
        print("测试计划:")
        print("  第1-3次: SendInput 点击窗口中心 (每次间隔2秒)")
        print("  第4-8次: PostMessage 点击窗口中心 (每次间隔2秒)")
        print("=" * 60)
        
        for i in range(1, 4):
            print(f"\n[第{i}/8次] SendInput 点击窗口中心...")
            bg_device.click_method = 'sendinput'
            bg_device.sendinput_restore_pos = False
            bg_device.touch((-1, -1), duration=0.1)
            print(f"[SUCCESS] SendInput 点击发送完成")
            
            if i < 3:
                time.sleep(2)
        
        print("\n------------------------------------------------")
        print("即将开始 PostMessage 测试")
        print("请观察游戏画面是否响应点击")
        print("------------------------------------------------")
        time.sleep(2)
        
        for i in range(4, 9):
            print(f"\n[第{i}/8次] PostMessage 点击窗口中心...")
            
            bg_device.click_method = 'postmessage'
            bg_device.touch((-1, -1), duration=0.1)
            
            print(f"[SUCCESS] PostMessage 点击发送完成")
            
            if i < 8:
                time.sleep(2)
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print(f"测试窗口对象: [{window_title}]")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
