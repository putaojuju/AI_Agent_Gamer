#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最终的嵌入窗口测试脚本
用于测试嵌入窗口的图像识别和点击功能
"""

import os
import sys
import time
import logging
from airtest.core.api import *
from airtest.core.win.win import Windows

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_embed_final.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def start_test_window():
    """提示用户启动测试窗口"""
    logger.info("=" * 60)
    logger.info("请先启动测试窗口")
    logger.info("=" * 60)
    logger.info("1. 打开一个新的终端")
    logger.info("2. 运行命令：python simple_test_window.py")
    logger.info("3. 确认测试窗口已启动")
    logger.info("\n测试窗口标题应为：'测试嵌入窗口'")
    logger.info("窗口包含一个'点击我'按钮和状态文本")
    logger.info("=" * 60)
    input("\n请完成上述操作后按Enter键继续...")

def take_button_screenshot():
    """截取按钮截图作为模板"""
    logger.info("\n" + "=" * 60)
    logger.info("截取按钮截图")
    logger.info("=" * 60)
    
    try:
        # 初始化Windows设备
        device = Windows()
        
        # 查找测试窗口
        test_window_title = "测试嵌入窗口"
        hwnd = device.get_handle_by_title(test_window_title)
        if not hwnd:
            logger.error(f"未找到测试窗口：{test_window_title}")
            return None
        
        logger.info(f"找到测试窗口，句柄：{hwnd}")
        
        # 连接设备
        connect_device(f"Windows:///{hwnd}")
        
        # 截取整个窗口
        window_screenshot = os.path.join(project_root, "window_screenshot.png")
        snapshot(filename=window_screenshot)
        logger.info(f"已截取窗口截图：{window_screenshot}")
        
        # 提示用户手动截取按钮
        logger.info("\n请使用Airtest IDE或其他工具从window_screenshot.png中截取按钮部分")
        button_template_path = os.path.join(project_root, "button_template.png")
        logger.info(f"将截取的按钮保存为：{button_template_path}")
        
        # 等待用户完成截图
        input("\n请按Enter键继续...")
        
        if not os.path.exists(button_template_path):
            logger.error(f"未找到按钮模板文件：{button_template_path}")
            return None
        
        logger.info(f"按钮模板已准备就绪：{button_template_path}")
        return button_template_path, hwnd
        
    except Exception as e:
        logger.error(f"截取按钮截图失败：{e}", exc_info=True)
        return None, None

def test_button_click(button_template_path, hwnd):
    """测试按钮点击功能"""
    logger.info("\n" + "=" * 60)
    logger.info("测试按钮点击功能")
    logger.info("=" * 60)
    
    try:
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
        
        # 截取结果截图
        result_screenshot = os.path.join(project_root, f"result_{int(time.time())}.png")
        snapshot(filename=result_screenshot)
        logger.info(f"已保存结果截图：{result_screenshot}")
        
        # 提示用户验证
        logger.info("\n请验证按钮是否被点击：")
        logger.info("1. 按钮文本应变为'已点击！'")
        logger.info("2. 上方状态文本应变为'按钮已被点击！'")
        logger.info(f"3. 可查看结果截图：{result_screenshot}")
        
        # 等待用户确认
        user_input = input("\n点击是否成功？(y/n): ")
        if user_input.lower() == 'y':
            logger.info("按钮点击成功！")
            return True
        else:
            logger.error("按钮点击失败")
            return False
            
    except Exception as e:
        logger.error(f"测试按钮点击失败：{e}", exc_info=True)
        return False

def test_embedded_mode(button_template_path):
    """测试嵌入模式"""
    logger.info("\n" + "=" * 60)
    logger.info("测试嵌入模式")
    logger.info("=" * 60)
    
    try:
        # 提示用户嵌入窗口
        logger.info("请将测试窗口嵌入到脚本管理器：")
        logger.info("1. 启动脚本管理器：python script_manager.py")
        logger.info("2. 在脚本管理器中点击'选择游戏窗口'按钮")
        logger.info("3. 将鼠标移动到测试窗口上，按下Alt键选择窗口")
        logger.info("4. 切换到'游戏嵌入'标签页")
        logger.info("5. 点击'嵌入游戏窗口'按钮")
        logger.info("\n等待窗口嵌入完成...")
        
        # 等待用户完成嵌入
        input("\n请完成上述操作后按Enter键继续...")
        
        # 查找嵌入后的窗口
        test_window_title = "测试嵌入窗口"
        device = Windows()
        hwnd = device.get_handle_by_title(test_window_title)
        if not hwnd:
            logger.error(f"未找到测试窗口：{test_window_title}")
            return False
        
        logger.info(f"找到嵌入后的测试窗口，句柄：{hwnd}")
        
        # 检查窗口是否被嵌入
        import win32gui
        parent_hwnd = win32gui.GetParent(hwnd)
        if parent_hwnd:
            logger.info(f"测试窗口已被嵌入，父窗口句柄：{parent_hwnd}")
        else:
            logger.warning("测试窗口未被嵌入")
        
        # 测试嵌入窗口的点击功能
        return test_button_click(button_template_path, hwnd)
        
    except Exception as e:
        logger.error(f"测试嵌入模式失败：{e}", exc_info=True)
        return False

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("嵌入窗口测试脚本")
    logger.info("=" * 60)
    
    try:
        # 1. 提示用户启动测试窗口
        start_test_window()
        
        # 2. 截取按钮截图
        button_template, hwnd = take_button_screenshot()
        if not button_template:
            logger.error("无法获取按钮模板，测试终止")
            return False
        
        # 3. 测试非嵌入模式
        if not test_button_click(button_template, hwnd):
            logger.error("非嵌入模式测试失败")
            return False
        
        # 4. 测试嵌入模式
        if not test_embedded_mode(button_template):
            logger.error("嵌入模式测试失败")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("所有测试通过！")
        logger.info("=" * 60)
        return True
        
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        return False
    except Exception as e:
        logger.error(f"测试发生意外错误：{e}", exc_info=True)
        return False

if __name__ == "__main__":
    main()
    input("\n请按Enter键退出...")