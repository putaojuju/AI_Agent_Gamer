#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的嵌入窗口测试脚本
自动创建测试窗口、截图按钮、测试点击功能
"""

import os
import sys
import time
import threading
import logging
from airtest.core.api import *
from airtest.core.win.win import Windows

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_embed_complete.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入Tkinter
import tkinter as tk
from tkinter import ttk

class EmbeddedTestWindow:
    """可嵌入的测试窗口类"""
    
    def __init__(self):
        """初始化测试窗口"""
        self.root = tk.Tk()
        self.root.title("测试嵌入窗口")
        self.root.geometry("400x300")
        self.root.resizable(True, True)
        
        # 设置窗口样式
        style = ttk.Style()
        style.theme_use("clam")
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加标题
        title_label = ttk.Label(main_frame, text="测试嵌入窗口", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 创建状态文本
        self.status_var = tk.StringVar(value="等待点击...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Arial", 12))
        self.status_label.pack(pady=(0, 20))
        
        # 创建测试按钮
        self.button = ttk.Button(
            main_frame, 
            text="点击我", 
            command=self.on_button_click,
            style="Accent.TButton",
            width=20
        )
        self.button.pack(pady=10)
        
        # 添加按钮提示
        hint_label = ttk.Label(main_frame, text="点击此按钮将改变上方文本", font=("Arial", 10, "italic"), foreground="gray")
        hint_label.pack(pady=(0, 20))
        
        # 添加嵌入状态标签
        self.embed_status_var = tk.StringVar(value="当前状态：未嵌入")
        embed_status_label = ttk.Label(main_frame, textvariable=self.embed_status_var, font=("Arial", 10), foreground="blue")
        embed_status_label.pack(pady=(0, 20))
        
        # 保存初始窗口信息
        self.original_parent = None
        self.is_embedded = False
        
        # 定期检查窗口状态
        self.check_embed_status()
        
        # 窗口句柄
        self.hwnd = None
    
    def on_button_click(self):
        """按钮点击事件处理"""
        # 改变按钮文本和状态
        current_text = self.button.cget("text")
        if current_text == "点击我":
            self.button.config(text="已点击！")
            self.status_var.set("按钮已被点击！")
        else:
            self.button.config(text="点击我")
            self.status_var.set("等待点击...")
    
    def check_embed_status(self):
        """检查窗口是否被嵌入"""
        import win32gui
        
        # 获取当前窗口句柄
        hwnd = win32gui.GetParent(self.root.winfo_id())
        
        if hwnd and not self.is_embedded:
            # 窗口已被嵌入
            self.is_embedded = True
            self.original_parent = hwnd
            self.embed_status_var.set(f"当前状态：已嵌入，父窗口句柄：{hwnd}")
        elif not hwnd and self.is_embedded:
            # 窗口已被取消嵌入
            self.is_embedded = False
            self.original_parent = None
            self.embed_status_var.set("当前状态：未嵌入")
        
        # 每2秒检查一次
        self.root.after(2000, self.check_embed_status)
    
    def run(self):
        """运行窗口主循环"""
        self.root.mainloop()
    
    def get_hwnd(self):
        """获取窗口句柄"""
        if not self.hwnd:
            import win32gui
            self.hwnd = win32gui.FindWindow(None, "测试嵌入窗口")
        return self.hwnd
    
    def reset_button(self):
        """重置按钮状态"""
        self.button.config(text="点击我")
        self.status_var.set("等待点击...")

def start_test_window():
    """启动测试窗口"""
    logger.info("启动测试窗口...")
    
    # 创建测试窗口
    test_window = EmbeddedTestWindow()
    
    # 在新线程中运行窗口
    window_thread = threading.Thread(target=test_window.run, daemon=True)
    window_thread.start()
    
    # 等待窗口启动
    time.sleep(2)
    logger.info("测试窗口已启动")
    
    return test_window

def take_button_screenshot(hwnd):
    """自动截取按钮截图"""
    logger.info("自动截取按钮截图...")
    
    try:
        # 连接设备
        connect_device(f"Windows:///{hwnd}")
        
        # 截取窗口
        window_screenshot = os.path.join(project_root, "window_screenshot.png")
        snapshot(filename=window_screenshot)
        logger.info(f"已截取窗口截图：{window_screenshot}")
        
        # 由于我们知道按钮的大致位置，直接截取固定区域
        # 注意：这个位置是基于窗口尺寸的，可能需要调整
        from PIL import Image
        
        # 打开截图
        img = Image.open(window_screenshot)
        
        # 按钮大致位置（基于400x300窗口）
        # 左上角坐标 (x1, y1), 右下角坐标 (x2, y2)
        button_region = (150, 150, 250, 180)  # 这个位置可能需要调整
        
        # 截取按钮
        button_img = img.crop(button_region)
        
        # 保存按钮模板
        button_template_path = os.path.join(project_root, "button_template.png")
        button_img.save(button_template_path)
        
        logger.info(f"已自动截取按钮模板：{button_template_path}")
        logger.info(f"按钮区域：{button_region}")
        
        return button_template_path
        
    except Exception as e:
        logger.error(f"自动截取按钮截图失败：{e}", exc_info=True)
        return None

def test_button_click(hwnd, button_template_path, test_window=None):
    """测试按钮点击"""
    logger.info("测试按钮点击功能...")
    
    try:
        # 重置按钮状态
        if test_window:
            test_window.reset_button()
            time.sleep(1)
        
        # 连接设备
        connect_device(f"Windows:///{hwnd}")
        
        # 查找按钮
        logger.info("使用图像识别查找按钮...")
        button_template = Template(button_template_path)
        
        # 尝试查找按钮
        button_pos = wait(button_template, timeout=10)
        if not button_pos:
            logger.error("未找到按钮")
            return False
        
        logger.info(f"成功找到按钮，位置：{button_pos}")
        
        # 点击按钮
        logger.info(f"点击按钮，位置：{button_pos}")
        touch(button_pos)
        
        # 等待状态变化
        time.sleep(1)
        
        # 验证点击是否成功
        logger.info("验证点击是否成功...")
        
        # 截取结果截图
        result_screenshot = os.path.join(project_root, f"result_{int(time.time())}.png")
        snapshot(filename=result_screenshot)
        logger.info(f"已保存结果截图：{result_screenshot}")
        
        # 使用窗口状态验证
        if test_window:
            status = test_window.status_var.get()
            logger.info(f"窗口状态：{status}")
            
            if "已被点击" in status:
                logger.info("按钮点击成功！")
                return True
            else:
                logger.error(f"按钮点击失败，当前状态：{status}")
                return False
        else:
            logger.info("请手动验证按钮是否被点击")
            return True
            
    except Exception as e:
        logger.error(f"测试按钮点击失败：{e}", exc_info=True)
        return False

def test_embedded_mode(button_template_path, test_window):
    """测试嵌入模式"""
    logger.info("测试嵌入模式...")
    
    try:
        # 提示用户嵌入窗口
        logger.info("\n" + "=" * 50)
        logger.info("请执行以下步骤将测试窗口嵌入到脚本管理器：")
        logger.info("1. 运行 script_manager.py")
        logger.info("2. 点击'选择游戏窗口'按钮")
        logger.info("3. 将鼠标移动到测试窗口上，按下Alt键选择窗口")
        logger.info("4. 切换到'游戏嵌入'标签页")
        logger.info("5. 点击'嵌入游戏窗口'按钮")
        logger.info("=" * 50)
        
        input("\n请完成上述操作后按Enter键继续...")
        
        # 获取窗口句柄
        hwnd = test_window.get_hwnd()
        if not hwnd:
            logger.error("未找到测试窗口句柄")
            return False
        
        # 检查窗口是否被嵌入
        import win32gui
        parent_hwnd = win32gui.GetParent(hwnd)
        if not parent_hwnd:
            logger.warning("测试窗口未被嵌入，继续测试...")
        else:
            logger.info(f"测试窗口已被嵌入，父窗口句柄：{parent_hwnd}")
        
        # 测试嵌入窗口的点击
        return test_button_click(hwnd, button_template_path, test_window)
        
    except Exception as e:
        logger.error(f"测试嵌入模式失败：{e}", exc_info=True)
        return False

def run_complete_test():
    """运行完整测试"""
    logger.info("=" * 60)
    logger.info("开始完整嵌入窗口测试")
    logger.info("=" * 60)
    
    # 1. 启动测试窗口
    test_window = start_test_window()
    
    # 2. 获取窗口句柄
    hwnd = test_window.get_hwnd()
    if not hwnd:
        logger.error("未找到测试窗口句柄")
        return False
    
    logger.info(f"测试窗口句柄：{hwnd}")
    
    # 3. 自动截取按钮截图
    button_template = take_button_screenshot(hwnd)
    if not button_template:
        logger.error("无法获取按钮模板")
        return False
    
    # 4. 测试非嵌入模式
    logger.info("\n" + "=" * 50)
    logger.info("测试非嵌入模式下的按钮点击")
    logger.info("=" * 50)
    
    if not test_button_click(hwnd, button_template, test_window):
        logger.error("非嵌入模式测试失败")
        return False
    
    # 5. 测试嵌入模式
    logger.info("\n" + "=" * 50)
    logger.info("测试嵌入模式下的按钮点击")
    logger.info("=" * 50)
    
    if not test_embedded_mode(button_template, test_window):
        logger.error("嵌入模式测试失败")
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成！所有测试通过！")
    logger.info("=" * 60)
    return True

if __name__ == "__main__":
    try:
        run_complete_test()
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
    except Exception as e:
        logger.error(f"测试发生意外错误：{e}", exc_info=True)
    
    input("\n请按Enter键退出...")