# -*- coding: utf-8 -*-
"""
测试脚本：验证后台模式是否正常工作
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

print("测试 background_windows 模块导入...")
try:
    from background_windows import BackgroundWindows
    print("✅ background_windows 模块导入成功")
except Exception as e:
    print(f"❌ background_windows 模块导入失败：{e}")
    sys.exit(1)

print("\n测试依赖模块导入...")
try:
    from virtual_display import virtual_display_manager
    print("✅ virtual_display 模块导入成功")
except Exception as e:
    print(f"❌ virtual_display 模块导入失败：{e}")

try:
    from independent_mouse import independent_mouse
    print("✅ independent_mouse 模块导入成功")
except Exception as e:
    print(f"❌ independent_mouse 模块导入失败：{e}")

try:
    from performance_monitor import performance_monitor
    print("✅ performance_monitor 模块导入成功")
except Exception as e:
    print(f"❌ performance_monitor 模块导入失败：{e}")

print("\n测试 Airtest API...")
try:
    import airtest.core.api as api
    print("✅ airtest.core.api 模块导入成功")
except Exception as e:
    print(f"❌ airtest.core.api 模块导入失败：{e}")

print("\n所有测试完成！")
