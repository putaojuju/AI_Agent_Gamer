# -*- coding: utf-8 -*-
"""
智能 Agent 核心调度器
将"脑"(AI)、"眼"(OCR)、"手"(BackgroundWindows)串联起来
"""

import time
import numpy as np
import cv2
import logging
from typing import Optional, Dict, Tuple
from PIL import Image

log_dir = "log"
import os
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'smart_agent.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('smart_agent')


class SmartAgent:
    """
    智能代理类，整合 AI 大脑、OCR 和后台操作
    
    功能：
    - 截图分析
    - 文字定位
    - 坐标转换
    - 操作执行
    - 结果验证
    """
    
    def __init__(self, background_windows, ai_brain, ocr_tool=None):
        """
        初始化智能代理
        
        Args:
            background_windows: BackgroundWindows 实例，用于截图和操作
            ai_brain: DoubaoBrain 实例，用于 AI 分析
            ocr_tool: OCRTool 实例，可选，如果为 None 则在需要时自动创建
        """
        self.bg_windows = background_windows
        self.ai_brain = ai_brain
        self.ocr_tool = ocr_tool
        self.history = []
        
        logger.info("智能代理初始化完成")
    
    def _ensure_ocr(self):
        """
        确保 OCR 工具已初始化
        """
        if self.ocr_tool is None:
            from ocr_tool import OCRTool
            self.ocr_tool = OCRTool()
            logger.info("OCR 工具已自动加载")
    
    def _calculate_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        计算两张图像的相似度（使用直方图方法）
        
        Args:
            img1: 第一张图像 (numpy 数组)
            img2: 第二张图像 (numpy 数组)
        
        Returns:
            相似度值 (0.0-1.0)
        """
        try:
            # 调整大小以加快计算
            size = (100, 100)
            img1_small = cv2.resize(img1, size)
            img2_small = cv2.resize(img2, size)
            
            # 计算直方图
            hist1 = cv2.calcHist([img1_small], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist2 = cv2.calcHist([img2_small], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            
            # 归一化
            hist1 = cv2.normalize(hist1, hist1).flatten()
            hist2 = cv2.normalize(hist2, hist2).flatten()
            
            # 计算相关性
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return float(correlation)
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    def _convert_ocr_to_window_coords(self, ocr_x: int, ocr_y: int) -> Tuple[int, int]:
        """
        将 OCR 返回的像素坐标转换为窗口相对坐标
        
        Args:
            ocr_x: OCR 返回的 X 像素坐标
            ocr_y: OCR 返回的 Y 像素坐标
        
        Returns:
            (rel_x, rel_y) 窗口相对坐标
        """
        try:
            import win32gui
            window_rect = win32gui.GetWindowRect(self.bg_windows.hwnd)
            window_left, window_top = window_rect[0], window_rect[1]
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]
            
            # OCR 返回的是截图中的像素坐标，已经是相对于窗口左上角的
            # 所以不需要再减去 window_left 和 window_top
            rel_x = ocr_x
            rel_y = ocr_y
            
            # 边界检查
            rel_x = max(0, min(window_width - 1, rel_x))
            rel_y = max(0, min(window_height - 1, rel_y))
            
            return rel_x, rel_y
        except Exception as e:
            logger.error(f"坐标转换失败: {e}")
            return ocr_x, ocr_y
    
    def _convert_ratio_to_window_coords(self, ratio_x: float, ratio_y: float) -> Tuple[int, int]:
        """
        将归一化坐标 (0.0-1.0) 转换为窗口相对坐标
        
        Args:
            ratio_x: 归一化 X 坐标
            ratio_y: 归一化 Y 坐标
        
        Returns:
            (rel_x, rel_y) 窗口相对坐标
        """
        try:
            import win32gui
            window_rect = win32gui.GetWindowRect(self.bg_windows.hwnd)
            window_width = window_rect[2] - window_rect[0]
            window_height = window_rect[3] - window_rect[1]
            
            rel_x = int(ratio_x * window_width)
            rel_y = int(ratio_y * window_height)
            
            # 边界检查
            rel_x = max(0, min(window_width - 1, rel_x))
            rel_y = max(0, min(window_height - 1, rel_y))
            
            return rel_x, rel_y
        except Exception as e:
            logger.error(f"坐标转换失败: {e}")
            return int(ratio_x * 1920), int(ratio_y * 1080)
    
    def _numpy_to_pil(self, img_array: np.ndarray) -> Image.Image:
        """
        将 numpy 数组转换为 PIL 图像
        
        Args:
            img_array: numpy 图像数组
        
        Returns:
            PIL 图像对象
        """
        if img_array is None:
            return None
        
        # 如果是 BGR 格式（OpenCV 默认），转换为 RGB
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
        
        return Image.fromarray(img_array)
    
    def step(self, task_instruction: str, verify: bool = True, wait_after_click: float = 1.0) -> Optional[Dict]:
        """
        执行一步智能操作
        
        Args:
            task_instruction: 任务指令，如"点击登录按钮"
            verify: 是否验证操作结果，默认 True
            wait_after_click: 点击后等待时间（秒），默认 1.0
        
        Returns:
            操作结果字典，包含：
            - success: 是否成功
            - action: 执行的操作
            - target: 目标坐标
            - target_text: 目标文字（如果有）
            - similarity: 操作前后相似度（如果验证）
            - message: 操作说明
        """
        logger.info(f"执行任务: {task_instruction}")
        
        try:
            # 1. 截图
            logger.info("正在截图...")
            screenshot_array = self.bg_windows.snapshot()
            if screenshot_array is None:
                logger.error("截图失败")
                return {"success": False, "action": "none", "message": "截图失败"}
            
            # 转换为 PIL 图像
            screenshot = self._numpy_to_pil(screenshot_array)
            if screenshot is None:
                logger.error("图像转换失败")
                return {"success": False, "action": "none", "message": "图像转换失败"}
            
            # 2. AI 分析
            logger.info("正在分析...")
            result = self.ai_brain.analyze(screenshot, task_instruction, save_debug=True, use_grid=True)
            
            if result is None:
                logger.error("AI 分析失败")
                return {"success": False, "action": "none", "message": "AI 分析失败"}
            
            action = result.get("action", "none")
            logger.info(f"AI 决策: action={action}, analysis={result.get('analysis', '')}")
            
            # 3. 根据决策执行操作
            if action == "none" or action == "wait":
                logger.info(f"无需操作或等待: {result.get('message', '')}")
                return {
                    "success": True,
                    "action": action,
                    "message": result.get("message", ""),
                    "target": None,
                    "target_text": None
                }
            
            if action == "stop":
                logger.warning(f"停止执行: {result.get('message', '')}")
                return {
                    "success": False,
                    "action": "stop",
                    "message": result.get("message", ""),
                    "target": None,
                    "target_text": None
                }
            
            if action == "click":
                # 保存操作前的截图用于验证
                before_screenshot = screenshot_array
                
                # 优先使用文字定位
                target_text = result.get("target_text")
                if target_text:
                    logger.info(f"使用文字定位: '{target_text}'")
                    self._ensure_ocr()
                    
                    ocr_result = self.ocr_tool.find_text(screenshot, target_text)
                    if ocr_result:
                        ocr_x, ocr_y, confidence = ocr_result
                        rel_x, rel_y = self._convert_ocr_to_window_coords(ocr_x, ocr_y)
                        
                        logger.info(f"OCR 找到文字，坐标: ({rel_x}, {rel_y}), 置信度: {confidence:.2f}")
                        
                        # 执行点击
                        click_result = self.bg_windows.touch((rel_x, rel_y))
                        
                        if not click_result:
                            logger.error("点击失败")
                            return {
                                "success": False,
                                "action": "click",
                                "target": (rel_x, rel_y),
                                "target_text": target_text,
                                "message": "点击失败"
                            }
                    else:
                        logger.warning(f"OCR 未找到文字 '{target_text}'，尝试使用坐标")
                        target = result.get("target")
                        if target and len(target) >= 2:
                            ratio_x, ratio_y = target[0], target[1]
                            rel_x, rel_y = self._convert_ratio_to_window_coords(ratio_x, ratio_y)
                            
                            logger.info(f"使用坐标点击: ({rel_x}, {rel_y})")
                            click_result = self.bg_windows.touch((rel_x, rel_y))
                            
                            if not click_result:
                                logger.error("点击失败")
                                return {
                                    "success": False,
                                    "action": "click",
                                    "target": (rel_x, rel_y),
                                    "target_text": None,
                                    "message": "点击失败"
                                }
                        else:
                            logger.error("没有可用的坐标")
                            return {
                                "success": False,
                                "action": "click",
                                "message": "没有可用的坐标"
                            }
                else:
                    # 使用坐标
                    target = result.get("target")
                    if target and len(target) >= 2:
                        ratio_x, ratio_y = target[0], target[1]
                        rel_x, rel_y = self._convert_ratio_to_window_coords(ratio_x, ratio_y)
                        
                        logger.info(f"使用坐标点击: ({rel_x}, {rel_y})")
                        click_result = self.bg_windows.touch((rel_x, rel_y))
                        
                        if not click_result:
                            logger.error("点击失败")
                            return {
                                "success": False,
                                "action": "click",
                                "target": (rel_x, rel_y),
                                "target_text": None,
                                "message": "点击失败"
                            }
                    else:
                        logger.error("没有可用的坐标")
                        return {
                            "success": False,
                            "action": "click",
                            "message": "没有可用的坐标"
                        }
                
                # 4. 验证操作结果
                similarity = None
                if verify:
                    logger.info(f"等待 {wait_after_click} 秒后验证...")
                    time.sleep(wait_after_click)
                    
                    after_screenshot = self.bg_windows.snapshot()
                    if after_screenshot is not None:
                        similarity = self._calculate_similarity(before_screenshot, after_screenshot)
                        logger.info(f"操作前后相似度: {similarity:.3f}")
                        
                        if similarity > 0.95:
                            logger.warning("警告：画面变化很小，操作可能无效")
                
                # 记录历史
                self.history.append({
                    "instruction": task_instruction,
                    "result": result,
                    "timestamp": time.time()
                })
                
                return {
                    "success": True,
                    "action": "click",
                    "target": (rel_x, rel_y) if 'rel_x' in locals() else None,
                    "target_text": target_text,
                    "similarity": similarity,
                    "message": result.get("message", "")
                }
            
            logger.warning(f"未知操作类型: {action}")
            return {
                "success": False,
                "action": action,
                "message": f"未知操作类型: {action}"
            }
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}", exc_info=True)
            return {
                "success": False,
                "action": "error",
                "message": str(e)
            }
    
    def run_sequence(self, instructions: list, verify: bool = True, wait_after_click: float = 1.0) -> list:
        """
        执行一系列任务指令
        
        Args:
            instructions: 指令列表，如 ["点击登录", "输入用户名", "点击确认"]
            verify: 是否验证操作结果
            wait_after_click: 点击后等待时间
        
        Returns:
            结果列表
        """
        results = []
        for i, instruction in enumerate(instructions, 1):
            logger.info(f"执行第 {i}/{len(instructions)} 步: {instruction}")
            result = self.step(instruction, verify, wait_after_click)
            results.append(result)
            
            # 如果遇到停止或失败，中断执行
            if result.get("action") == "stop":
                logger.warning("收到停止指令，中断执行")
                break
            if not result.get("success"):
                logger.warning(f"第 {i} 步执行失败，中断执行")
                break
        
        return results


if __name__ == "__main__":
    print("智能代理模块测试")
    print("使用示例:")
    print("""
    from smart_agent import SmartAgent
    from background_windows import BackgroundWindows
    from ai_brain import DoubaoBrain
    from airtest.core.api import auto_setup
    
    # 初始化
    api.auto_setup(__file__, devices=["Windows:///"])
    dev = api.device()
    bg_windows = BackgroundWindows(dev)
    bg_windows.init_hwnd(hwnd)
    
    ai_brain = DoubaoBrain(api_key="your_key", endpoint_id="ep-xxxxx")
    agent = SmartAgent(bg_windows, ai_brain)
    
    # 执行单步任务
    result = agent.step("点击登录按钮")
    print(result)
    
    # 执行任务序列
    results = agent.run_sequence(["点击登录", "输入密码", "点击确认"])
    for r in results:
        print(r)
    """)
