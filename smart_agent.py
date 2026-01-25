import threading
import base64
import io
from PIL import Image
import numpy as np
import win32gui
from typing import Optional, Dict, Any
from game_window import GameWindow
from mouse_controller import MouseController
from ai_brain import AIBrain
from config_manager import ConfigManager
import time
from vision_core import VisionCore

class SmartAgent:
    def __init__(self, ui_queue: Optional[Any] = None, game_window: Optional[GameWindow] = None):
        self.game_window = game_window if game_window else GameWindow()
        self.mouse_controller = MouseController()
        self.ai_brain = AIBrain()
        self.config_manager = ConfigManager()
        self.ui_queue = ui_queue
        self.running = False
    
    def _image_to_base64(self, image_array: np.ndarray) -> str:
        """将图像数组转换为base64编码"""
        try:
            # 转换为PIL图像
            img = Image.fromarray(image_array)
            
            # 保存到内存缓冲区
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            
            # 编码为base64
            base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return base64_data
        except Exception:
            return ""
    
    def _normalize_to_pixel(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        """将归一化坐标 (0.0-1.0) 转换为实际窗口像素坐标
        
        修正：使用客户区尺寸（去掉标题栏），确保与截图范围一致
        """
        if not self.game_window.hwnd:
            return 0, 0
        
        # 获取客户区尺寸（去掉标题栏和边框）
        try:
            left, top, right, bottom = win32gui.GetClientRect(self.game_window.hwnd)
            w = right - left
            h = bottom - top
        except Exception:
            # 降级方案：使用窗口尺寸
            if not self.game_window.width or not self.game_window.height:
                rect = win32gui.GetWindowRect(self.game_window.hwnd)
                w = rect[2] - rect[0]
                h = rect[3] - rect[1]
            else:
                w, h = self.game_window.width, self.game_window.height
        
        # 确保尺寸有效
        if w <= 0 or h <= 0:
            return 0, 0
            
        pixel_x = int(norm_x * w)
        pixel_y = int(norm_y * h)
        return pixel_x, pixel_y
    
    def start(self, window_title: Optional[str] = None):
        """启动智能代理"""
        if window_title is not None:
            success = self.game_window.init_hwnd(window_title)
            if not success:
                if self.ui_queue:
                    self.ui_queue.put({"text": f"无法找到游戏窗口: {window_title}", "type": "error"})
                return False
        else:
            # 如果window_title为None，信任现有的self.game_window.hwnd
            if not self.game_window.hwnd:
                if self.ui_queue:
                    self.ui_queue.put({"text": "游戏窗口未初始化，请先连接窗口", "type": "error"})
                return False
        
        self.running = True
        self.agent_thread = threading.Thread(target=self.run, daemon=True)
        self.agent_thread.start()
        
        if self.ui_queue:
            if window_title:
                self.ui_queue.put({"text": f"智能代理已启动，正在监控游戏窗口: {window_title}", "type": "success"})
            else:
                self.ui_queue.put({"text": "智能代理已启动，正在监控已连接的游戏窗口", "type": "success"})
        
        return True
    
    def stop(self):
        """停止智能代理"""
        self.running = False
        if hasattr(self, "agent_thread") and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=2)
        
        if self.ui_queue:
            self.ui_queue.put({"text": "智能代理已停止", "type": "info"})
    
    def run(self):
        """代理主循环"""
        while self.running:
            try:
                # 获取游戏窗口截图
                screenshot = self.game_window.snapshot()
                if screenshot is None:
                    if self.ui_queue:
                        self.ui_queue.put({"text": "无法获取游戏窗口截图", "type": "warning"})
                    continue
                
                # 分析游戏状态
                analysis = self.step(screenshot)
                
                # 根据分析结果执行相应的操作
                action_type = analysis.get("action_type")
                if action_type == "click":
                    target = analysis.get("target")
                    if target:
                        self.execute_action("click", target[0], target[1])
                
            except Exception as e:
                if self.ui_queue:
                    self.ui_queue.put({"text": f"代理运行出错: {str(e)}", "type": "error"})
            
            # 控制循环频率
            time.sleep(1)
    
    def step(self, image_data: np.ndarray) -> Dict[str, Any]:
        """执行单步分析和决策"""
        # 1. 将图像转换为base64
        image_base64 = self._image_to_base64(image_data)
        if not image_base64:
            if self.ui_queue:
                self.ui_queue.put({"text": "无法转换图像为base64", "type": "error"})
            return {
                "ai_analysis": {"success": False, "error": "图像转换失败"},
                "ocr_results": [],
                "timestamp": time.time()
            }
        
        # 2. 使用AI分析图像
        ai_result = self.ai_brain.analyze(image_base64)
        
        # 3. 解析AI结果
        result = {
            "ai_analysis": ai_result,
            "ocr_results": [],
            "timestamp": time.time(),
            "action_type": None,
            "target": None
        }
        
        if ai_result.get("success"):
            ai_data = ai_result.get("data", {})
            thought = ai_data.get("thought", "")
            action_type = ai_data.get("action")
            target_norm = ai_data.get("target")
            confidence = ai_data.get("confidence", 0.0)
            reason = ai_data.get("reason", "")
            
            # 输出AI思考过程
            if self.ui_queue:
                self.ui_queue.put({"text": f"AI思考: {thought}", "type": "thought"})
                if reason:
                    self.ui_queue.put({"text": f"AI理由: {reason}", "type": "info"})
                
            # 执行动作 (Seed 1.8 优先模式)
            if action_type == "click" and target_norm:
                # 坐标转换
                px, py = self._normalize_to_pixel(target_norm[0], target_norm[1])
                
                if self.ui_queue:
                    self.ui_queue.put({"text": f"视觉定位: ({target_norm[0]:.2f}, {target_norm[1]:.2f}) -> ({px}, {py})", "type": "vision"})
                    self.ui_queue.put({"text": f"执行点击操作，置信度: {confidence:.2f}", "type": "action"})
                
                # 更新结果
                result["action_type"] = "click"
                result["target"] = [px, py]
                
            elif action_type == "wait":
                if self.ui_queue:
                    self.ui_queue.put({"text": "AI建议等待...", "type": "info"})
                
            else:
                # [混合双打逻辑] 如果 AI 没给出坐标，尝试 OCR 兜底
                if self.ui_queue:
                    self.ui_queue.put({"text": "未获取视觉坐标，尝试 OCR 兜底...", "type": "warning"})
                
                # OCR 补救: 从思考或理由中提取关键词
                ocr_targets = []
                if thought:
                    # 提取可能的按钮文本
                    import re
                    buttons = re.findall(r'点击[“"]([^"”]+)["”]', thought)
                    ocr_targets.extend(buttons)
                if reason:
                    buttons = re.findall(r'点击[“"]([^"”]+)["”]', reason)
                    ocr_targets.extend(buttons)
                
                # 尝试OCR识别
                if ocr_targets:
                    if self.ui_queue:
                        self.ui_queue.put({"text": f"OCR识别目标: {ocr_targets}", "type": "info"})
                    
                    # 创建视觉核心实例
                    vision = VisionCore(hwnd=self.game_window.hwnd)
                    
                    # 查找第一个匹配的文本
                    for target_text in ocr_targets:
                        ocr_result = vision.find_text(target_text)
                        if ocr_result:
                            x, y, conf = ocr_result
                            if self.ui_queue:
                                self.ui_queue.put({"text": f"OCR识别成功: '{target_text}' at ({x}, {y}), 置信度: {conf:.2f}", "type": "success"})
                            # 更新结果
                            result["action_type"] = "click"
                            result["target"] = [x, y]
                            break
                
        else:
            if self.ui_queue:
                self.ui_queue.put({
                    "text": "AI分析失败", 
                    "type": "error", 
                    "detail": ai_result.get("error", "")
                })
        
        return result
    
    def execute_action(self, action: str, x: int, y: int) -> bool:
        """执行操作"""
        if not self.game_window.hwnd:
            if self.ui_queue:
                self.ui_queue.put({"text": "游戏窗口未连接", "type": "error"})
            return False
        
        try:
            if action == "click":
                success = self.mouse_controller.click(x, y, self.game_window.hwnd)
            elif action == "double_click":
                success = self.mouse_controller.double_click(x, y, self.game_window.hwnd)
            elif action == "right_click":
                success = self.mouse_controller.right_click(x, y, self.game_window.hwnd)
            elif action == "move":
                success = self.mouse_controller.move(x, y, self.game_window.hwnd)
            else:
                success = False
            
            if self.ui_queue:
                if success:
                    self.ui_queue.put({"text": f"执行操作成功: {action} at ({x}, {y})", "type": "success"})
                else:
                    self.ui_queue.put({"text": f"执行操作失败: {action} at ({x}, {y})", "type": "error"})
            
            return success
        except Exception as e:
            if self.ui_queue:
                self.ui_queue.put({"text": f"执行操作出错: {str(e)}", "type": "error"})
            return False
