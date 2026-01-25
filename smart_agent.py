import threading
import base64
import io
from PIL import Image
import numpy as np
from typing import Optional, Dict, Any
from game_window import GameWindow
from mouse_controller import MouseController
from ai_brain import AIBrain
from config_manager import ConfigManager
import time

class SmartAgent:
    def __init__(self, ui_queue: Optional[Any] = None):
        self.game_window = GameWindow()
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
    
    def start(self, window_title: str):
        """启动智能代理"""
        success = self.game_window.init_hwnd(window_title)
        if not success:
            if self.ui_queue:
                self.ui_queue.put({"text": f"无法找到游戏窗口: {window_title}", "type": "error"})
            return False
        
        self.running = True
        self.agent_thread = threading.Thread(target=self.run, daemon=True)
        self.agent_thread.start()
        
        if self.ui_queue:
            self.ui_queue.put({"text": f"智能代理已启动，正在监控游戏窗口: {window_title}", "type": "success"})
        
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
                
                # 这里可以根据分析结果执行相应的操作
                # 例如：点击、移动鼠标等
                
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
        
        # 3. 将AI的raw_response作为detail参数传给ui_queue
        if self.ui_queue:
            if ai_result.get("success"):
                self.ui_queue.put({
                    "text": "AI分析完成", 
                    "type": "thought", 
                    "detail": str(ai_result.get("raw_response", ""))
                })
            else:
                self.ui_queue.put({
                    "text": "AI分析失败", 
                    "type": "error", 
                    "detail": ai_result.get("error", "")
                })
        
        # 4. 模拟OCR结果
        ocr_results = ["角色: 100/100", "敌人: 50/100", "物品: 3"]
        
        # 5. 将OCR结果作为detail参数传给ui_queue
        if self.ui_queue:
            self.ui_queue.put({
                "text": "OCR识别完成", 
                "type": "info", 
                "detail": "\n".join(ocr_results)
            })
        
        # 6. 构建返回结果
        return {
            "ai_analysis": ai_result,
            "ocr_results": ocr_results,
            "timestamp": time.time()
        }
    
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
