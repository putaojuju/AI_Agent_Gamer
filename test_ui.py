# -*- coding: utf-8 -*-
"""
UI 测试脚本
测试新的 CustomTkinter UI 框架
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import AICmdCenter

if __name__ == "__main__":
    print("启动 UI 测试...")
    print("测试内容:")
    print("1. 基础 UI 框架启动")
    print("2. 左侧导航栏功能")
    print("3. 右侧主面板布局")
    print("4. 测试截图功能")
    print("5. 性能和响应速度")
    print("\n按 Ctrl+C 退出测试")
    
    try:
        app = AICmdCenter()
        app.mainloop()
    except Exception as e:
        print(f"测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()