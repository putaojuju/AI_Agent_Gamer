# -*- coding: utf-8 -*-
"""
测试脚本：往窗口正中央发送PostMessage鼠标点击
发送间隔4秒，循环4次之后脚本结束
"""
import sys
import os
import time
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from airtest.core.win.win import Windows
from background_windows import BackgroundWindows
import win32gui
import win32api

def main():
    print("=" * 60)
    print("PostMessage 点击测试脚本")
    print("=" * 60)
    
    try:
        print("\n[1/4] 初始化 Windows 设备...")
        device = Windows()
        print("[SUCCESS] Windows 设备初始化成功")
        
        print("\n[2/4] 查找目标窗口...")
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            print("[ERROR] 未找到活动窗口")
            return False
        
        print(f"[SUCCESS] 找到窗口句柄: {hwnd}")
        
        print("\n[3/4] 初始化后台模式...")
        bg_device = BackgroundWindows(device)
        bg_device.init_hwnd(hwnd)
        print("[SUCCESS] 后台模式初始化成功")
        
        window_rect = win32gui.GetWindowRect(hwnd)
        width = window_rect[2] - window_rect[0]
        height = window_rect[3] - window_rect[1]
        center_x = window_rect[0] + width // 2
        center_y = window_rect[1] + height // 2
        print(f"[SUCCESS] 窗口尺寸: {width}x{height}")
        print(f"[SUCCESS] 窗口中心坐标: ({center_x}, {center_y})")
        
        print("\n[4/4] 开始点击测试...")
        print("循环次数: 4")
        print("间隔时间: 4秒")
        print("-" * 60)
        
        for i in range(1, 5):
            print(f"\n第 {i}/4 次点击 [{time.strftime('%H:%M:%S')}]")
            
            try:
                if i == 1:
                    print("使用 SendInput 方式点击 (不恢复鼠标位置)...")
                    bg_device.click_method = 'sendinput'
                    bg_device.sendinput_restore_pos = False
                    bg_device.touch((-1, -1), duration=0.1)
                else:
                    print("使用 PostMessage 方式点击 (使用当前鼠标位置)...")
                    bg_device.click_method = 'postmessage'
                    
                    # 获取当前鼠标位置
                    mouse_pos = win32api.GetCursorPos()
                    print(f"当前鼠标位置: {mouse_pos}")
                    
                    # 转换为相对于窗口左上角的坐标
                    rel_x = mouse_pos[0] - window_rect[0]
                    rel_y = mouse_pos[1] - window_rect[1]
                    print(f"相对窗口坐标: ({rel_x}, {rel_y})")
                    
                    # 使用相对坐标点击
                    bg_device.touch((rel_x, rel_y), duration=0.1)
                
                print(f"[SUCCESS] 点击发送成功")
            except Exception as e:
                print(f"[ERROR] 点击发送失败: {e}")
            
            if i < 4:
                print(f"等待 4 秒...")
                time.sleep(4)
        
        print("\n" + "=" * 60)
        print("测试完成！共执行 4 次点击")
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
