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
        """将归一化坐标转换为屏幕绝对坐标
        
        修正：使用ClientToScreen转换，确保鼠标点击到正确的屏幕位置
        """
        if not self.game_window.hwnd:
            return 0, 0
        
        try:
            # 1. 获取客户区的大小 (用于计算相对位置)
            left, top, right, bottom = win32gui.GetClientRect(self.game_window.hwnd)
            w = right - left
            h = bottom - top
            
            # 2. 计算相对于客户区左上角的像素坐标
            rel_x = int(norm_x * w)
            rel_y = int(norm_y * h)
            
            # 3. [关键修正] 将客户区坐标 (0,0) 转换为屏幕坐标
            # ClientToScreen 会自动计算标题栏和边框的高度偏移
            client_point = (0, 0)
            screen_origin = win32gui.ClientToScreen(self.game_window.hwnd, client_point)
            screen_x_start, screen_y_start = screen_origin
            
            # 4. 最终屏幕坐标 = 屏幕原点 + 相对坐标
            final_x = screen_x_start + rel_x
            final_y = screen_y_start + rel_y
            
            return final_x, final_y
            
        except Exception as e:
            if self.ui_queue:
                self.ui_queue.put({"title": f"坐标转换错误: {e}", "type": "ERROR"})
            return 0, 0
    
    def start(self, window_title: Optional[str] = None):
        """启动智能代理"""
        if window_title is not None:
            success = self.game_window.init_hwnd(window_title)
            if not success:
                if self.ui_queue:
                    self.ui_queue.put({"title": f"无法找到游戏窗口: {window_title}", "type": "ERROR"})
                return False
        else:
            # 如果window_title为None，信任现有的self.game_window.hwnd
            if not self.game_window.hwnd:
                if self.ui_queue:
                    self.ui_queue.put({"title": "游戏窗口未初始化，请先连接窗口", "type": "ERROR"})
                return False
        
        self.running = True
        self.agent_thread = threading.Thread(target=self.run, daemon=True)
        self.agent_thread.start()
        
        if self.ui_queue:
            if window_title:
                self.ui_queue.put({"title": f"智能代理已启动，正在监控游戏窗口: {window_title}", "type": "SYSTEM"})
            else:
                self.ui_queue.put({"title": "智能代理已启动，正在监控已连接的游戏窗口", "type": "SYSTEM"})
        
        return True
    
    def stop(self):
        """停止智能代理"""
        self.running = False
        if hasattr(self, "agent_thread") and self.agent_thread.is_alive():
            self.agent_thread.join(timeout=2)
        
        if self.ui_queue:
            self.ui_queue.put({"title": "智能代理已停止", "type": "SYSTEM"})
    
    def run(self):
        """代理主循环"""
        while self.running:
            try:
                # 获取游戏窗口截图
                screenshot = self.game_window.snapshot()
                if screenshot is None:
                    if self.ui_queue:
                        self.ui_queue.put({"title": "无法获取游戏窗口截图", "type": "WARNING"})
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
                import traceback
                if self.ui_queue:
                    self.ui_queue.put({"title": f"代理运行出错: {str(e)}", "type": "ERROR", "detail": traceback.format_exc()})
            
            # 控制循环频率
            time.sleep(1)
    
    def step(self, image_data: np.ndarray) -> Dict[str, Any]:
        """执行单步分析和决策"""
        # 1. 将图像转换为base64
        image_base64 = self._image_to_base64(image_data)
        if not image_base64:
            if self.ui_queue:
                self.ui_queue.put({"title": "无法转换图像为base64", "type": "ERROR"})
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
                self.ui_queue.put({
                    "type": "THOUGHT",
                    "title": f"AI 思考中: {thought[:20]}..." if thought else "AI 分析中...",
                    "detail": f"完整思考:\n{thought}\n\n原始数据:\n{ai_data}"
                })
                if reason:
                    self.ui_queue.put({"title": f"AI理由: {reason}", "type": "SYSTEM"})
                
            # 执行动作 (Seed 1.8 优先模式)
            if action_type == "click" and target_norm:
                # 坐标转换
                px, py = self._normalize_to_pixel(target_norm[0], target_norm[1])
                
                if self.ui_queue:
                    # 视觉定位日志
                    self.ui_queue.put({
                        "type": "VISION",
                        "title": f"定位目标: ({px}, {py})",
                        "detail": f"归一化坐标: {target_norm}\n窗口尺寸: {self.game_window.width}x{self.game_window.height}\n置信度: {confidence}"
                    })
                    # 执行动作日志
                    self.ui_queue.put({
                        "type": "ACTION",
                        "title": f"执行点击 -> {px}, {py}",
                        "detail": f"Action Type: {action_type}\nReason: {reason}"
                    })
                
                # 更新结果
                result["action_type"] = "click"
                result["target"] = [px, py]
                
            elif action_type == "wait":
                if self.ui_queue:
                    self.ui_queue.put({"title": "AI建议等待...", "type": "SYSTEM"})
                
            else:
                # [混合双打逻辑] 如果 AI 没给出坐标，尝试 OCR 兜底
                if self.ui_queue:
                    self.ui_queue.put({"title": "未获取视觉坐标，尝试 OCR 兜底...", "type": "WARNING"})
                
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
                        self.ui_queue.put({"title": f"OCR识别目标: {ocr_targets}", "type": "SYSTEM"})
                    
                    # 创建视觉核心实例
                    vision = VisionCore(hwnd=self.game_window.hwnd)
                    
                    # 查找第一个匹配的文本
                    for target_text in ocr_targets:
                        ocr_result = vision.find_text(target_text)
                        if ocr_result:
                            x, y, conf = ocr_result
                            if self.ui_queue:
                                self.ui_queue.put({"title": f"OCR识别成功: '{target_text}' at ({x}, {y}), 置信度: {conf:.2f}", "type": "VISION"})
                            # 更新结果
                            result["action_type"] = "click"
                            result["target"] = [x, y]
                            break
                
        else:
            if self.ui_queue:
                self.ui_queue.put({
                    "title": "AI分析失败", 
                    "type": "ERROR", 
                    "detail": ai_result.get("error", "")
                })
        
        return result
    
    def execute_action(self, action: str, x: int, y: int) -> bool:
        """执行操作"""
        if not self.game_window.hwnd:
            if self.ui_queue:
                self.ui_queue.put({"title": "游戏窗口未连接", "type": "ERROR"})
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
                    self.ui_queue.put({"title": f"执行操作成功: {action} at ({x}, {y})", "type": "ACTION"})
                else:
                    self.ui_queue.put({"title": f"执行操作失败: {action} at ({x}, {y})", "type": "ERROR"})
            
            return success
        except Exception as e:
            import traceback
            if self.ui_queue:
                self.ui_queue.put({"title": f"执行操作出错: {str(e)}", "type": "ERROR", "detail": traceback.format_exc()})
            return False
