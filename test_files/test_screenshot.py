# -*- coding: utf-8 -*-
"""
简单的截图测试脚本
用于调试截图功能
"""

import win32gui
import mss
import numpy as np
import time

# 设置要测试的窗口标题
target_title = "测试窗口"

def test_screenshot():
    print("=" * 50)
    print("截图测试脚本")
    print("=" * 50)
    
    # 查找窗口
    hwnd = win32gui.FindWindow(None, target_title)
    if hwnd == 0:
        print(f"未找到窗口：{target_title}")
        return False
    
    print(f"找到窗口，句柄：{hwnd}")
    
    # 检查窗口是否可见
    is_visible = win32gui.IsWindowVisible(hwnd)
    print(f"窗口可见：{is_visible}")
    
    if not is_visible:
        print("尝试显示窗口...")
        win32gui.ShowWindow(hwnd, win32gui.SW_SHOW)
        time.sleep(0.5)
        is_visible = win32gui.IsWindowVisible(hwnd)
        print(f"窗口可见：{is_visible}")
    
    # 获取窗口矩形
    rect = win32gui.GetWindowRect(hwnd)
    print(f"窗口矩形：{rect}")
    
    left, top, right, bottom = rect
    width = right - left
    height = bottom - top
    
    print(f"窗口尺寸：{width}x{height}")
    
    # 使用mss截图
    print("\n使用mss截图：")
    with mss.mss() as sct:
        # 定义截图区域
        monitor = {
            "top": top,
            "left": left,
            "width": width,
            "height": height
        }
        print(f"截图区域：{monitor}")
        
        # 截图
        sct_img = sct.grab(monitor)
        print(f"mss.grab返回类型：{type(sct_img)}")
        print(f"mss.grab返回值：{sct_img}")
        
        # 转换为numpy数组
        screen = np.array(sct_img, dtype=np.uint8)
        print(f"转换为numpy数组：")
        print(f"  类型：{type(screen)}")
        print(f"  形状：{screen.shape if hasattr(screen, 'shape') else 'no shape'}")
        print(f"  大小：{screen.size if hasattr(screen, 'size') else 'no size'}")
        
        if screen.size > 0:
            print("截图成功！")
            # 只保留RGB通道
            if screen.shape[-1] >= 3:
                screen = screen[..., :3]
                print(f"RGB通道形状：{screen.shape}")
            return True
        else:
            print("截图失败，返回空数组")
            return False

if __name__ == "__main__":
    test_screenshot()
