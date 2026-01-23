# -*- coding: utf-8 -*-
"""
AI 大脑模块 - 豆包视觉模型集成
使用豆包-1.8-Vision 模型实现游戏画面的智能分析和决策
"""

import base64
import json
import io
import os
from datetime import datetime
from typing import Dict, Optional, Tuple
from PIL import Image, ImageDraw
from openai import OpenAI


class DoubaoBrain:
    """
    豆包 AI 大脑类
    
    通过火山引擎 Ark 平台的 OpenAI 兼容接口，
    实现游戏画面的视觉分析和智能决策
    """
    
    def __init__(self, api_key: str, endpoint_id: str, model_name: str = "Doubao-1.8-Pro"):
        """
        初始化 AI 大脑
        
        Args:
            api_key: 火山引擎 API Key
            endpoint_id: 模型端点 ID (如 ep-20240501000000-abcde)
            model_name: 模型名称
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://ark.cn-beijing.volces.com/api/v3"
        )
        self.model = endpoint_id
        self.model_name = model_name
        self.history = []
        
        # 调试快照目录
        self.debug_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "logs",
            "ai_snapshots"
        )
        os.makedirs(self.debug_dir, exist_ok=True)
        
        # 系统提示词
        self.system_prompt = """
你是一个专业的游戏自动化助手。请分析截图并根据指令做出决策。

必须返回纯 JSON 格式，不要包含 Markdown 标记或其他多余文字：
{
    "analysis": "分析当前界面状态...",
    "action": "click" | "wait" | "stop" | "none",
    "target_text": "按钮上的文字",  // 优先：如果是包含文字的按钮，请返回按钮上的文字
    "target": [x_ratio, y_ratio],  // 备用：如果没有文字或无法识别，再用坐标 (0.0-1.0)
    "message": "简短的操作说明",
    "confidence": 0.0-1.0  // 置信度
}

规则：
1. 如果是包含文字的按钮，请优先返回 target_text 字段，而不是 target 坐标
2. target_text 应该是按钮上显示的完整文字，如"开始行动"、"确认"、"签到"等
3. 如果无法识别文字或按钮没有文字，再使用 target 坐标
4. 如果无法识别或需要等待，action 设为 "wait"
5. 如果遇到致命错误或无法处理的情况，action 设为 "stop"
6. 如果当前状态正常无需操作，action 设为 "none"
7. target 坐标使用归一化格式 (0.0-1.0)，左上角为 (0,0)，右下角为 (1,1)
8. confidence 表示你对决策的信心程度 (0.0-1.0)
9. 截图上已绘制辅助网格，帮助你更准确地估算坐标（当 OCR 无法使用时）
"""
    
    def _add_grid_overlay(self, image: Image.Image, grid_size: int = 4) -> Image.Image:
        """
        在图像上添加辅助网格，帮助 AI 更准确地估算坐标
        
        Args:
            image: PIL 图像对象
            grid_size: 网格大小 (3 或 4)，默认 4
        
        Returns:
            添加了网格的 PIL 图像对象
        """
        img_width, img_height = image.size
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 网格颜色：半透明红色
        grid_color = (255, 0, 0, 80)
        axis_color = (255, 0, 0, 150)
        
        # 绘制垂直线
        for i in range(1, grid_size):
            x = int(img_width * i / grid_size)
            draw.line([(x, 0), (x, img_height)], fill=grid_color, width=1)
        
        # 绘制水平线
        for i in range(1, grid_size):
            y = int(img_height * i / grid_size)
            draw.line([(0, y), (img_width, y)], fill=grid_color, width=1)
        
        # 绘制坐标轴（左上角）
        axis_length = min(img_width, img_height) // 10
        draw.line([(0, 0), (axis_length, 0)], fill=axis_color, width=2)
        draw.line([(0, 0), (0, axis_length)], fill=axis_color, width=2)
        
        # 添加坐标标记
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
        
        draw.text((5, 5), "X", fill=axis_color, font=font)
        draw.text((5, 15), "Y", fill=axis_color, font=font)
        
        return image
    
    def _image_to_base64(self, image: Image.Image, max_size: int = 1280) -> str:
        """
        将 PIL 图像转换为 Base64 字符串
        
        Args:
            image: PIL 图像对象
            max_size: 最大边长（用于压缩以节省 Token）
        
        Returns:
            Base64 编码的 JPEG 图像字符串
        """
        # 如果图像过大，进行压缩
        if max(image.size) > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 转换为 JPEG 格式并压缩
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """
        解析 AI 返回的 JSON 响应
        
        Args:
            content: AI 返回的原始内容
        
        Returns:
            解析后的 JSON 字典，失败返回 None
        """
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 Markdown 代码块中的 JSON
            if "```json" in content:
                try:
                    json_str = content.split("```json")[1].split("```")[0]
                    return json.loads(json_str.strip())
                except (IndexError, json.JSONDecodeError):
                    pass
            elif "```" in content:
                try:
                    json_str = content.split("```")[1].split("```")[0]
                    return json.loads(json_str.strip())
                except (IndexError, json.JSONDecodeError):
                    pass
            
            # 尝试查找第一个 { 和最后一个 } 之间的内容
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                try:
                    return json.loads(content[start:end+1])
                except json.JSONDecodeError:
                    pass
        
        return None
    
    def _save_debug_snapshot(self, image: Image.Image, result: Dict):
        """
        保存调试快照
        
        Args:
            image: 原始截图
            result: AI 分析结果
        """
        try:
            # 生成文件名：时间戳_动作_目标.jpg
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            action = result.get("action", "unknown")
            target = result.get("target", [0, 0])
            filename = f"{timestamp}_{action}_{target[0]:.2f}_{target[1]:.2f}.jpg"
            filepath = os.path.join(self.debug_dir, filename)
            
            # 复制图像用于标注
            debug_image = image.copy()
            draw = ImageDraw.Draw(debug_image)
            
            # 如果有点击目标，绘制红色圆圈
            if action == "click" and result.get("target"):
                img_width, img_height = image.size
                x = int(result["target"][0] * img_width)
                y = int(result["target"][1] * img_height)
                radius = min(img_width, img_height) // 20
                draw.ellipse(
                    [x - radius, y - radius, x + radius, y + radius],
                    outline="red",
                    width=3
                )
                draw.line([x - radius - 10, y, x - radius, y], fill="red", width=2)
                draw.line([x, y - radius - 10, x, y - radius], fill="red", width=2)
            
            # 保存快照
            debug_image.save(filepath, quality=90)
            
            # 自动清理：超过 100 张时删除最旧的
            snapshots = sorted(
                [f for f in os.listdir(self.debug_dir) if f.endswith('.jpg')],
                key=lambda x: os.path.getmtime(os.path.join(self.debug_dir, x))
            )
            while len(snapshots) > 100:
                oldest = snapshots.pop(0)
                os.remove(os.path.join(self.debug_dir, oldest))
                
        except Exception as e:
            print(f"保存调试快照失败: {e}")
    
    def normalize_to_pixel(self, norm_x: float, norm_y: float, window_width: int, window_height: int) -> Tuple[int, int]:
        """
        将归一化坐标转换为像素坐标
        
        Args:
            norm_x: 归一化 X 坐标 (0.0-1.0)
            norm_y: 归一化 Y 坐标 (0.0-1.0)
            window_width: 窗口宽度（像素）
            window_height: 窗口高度（像素）
        
        Returns:
            (pixel_x, pixel_y) 像素坐标
        """
        pixel_x = int(norm_x * window_width)
        pixel_y = int(norm_y * window_height)
        
        # 边界限制
        pixel_x = max(0, min(window_width - 1, pixel_x))
        pixel_y = max(0, min(window_height - 1, pixel_y))
        
        return pixel_x, pixel_y
    
    def analyze(self, screenshot: Image.Image, instruction: str, save_debug: bool = True, use_grid: bool = True) -> Optional[Dict]:
        """
        分析截图并返回决策
        
        Args:
            screenshot: PIL 图像对象
            instruction: 用户指令
            save_debug: 是否保存调试快照
            use_grid: 是否添加辅助网格，默认 True
        
        Returns:
            分析结果字典，包含：
            - analysis: 界面分析
            - action: 操作类型 (click/wait/stop/none)
            - target_text: 目标文字（如果有）
            - target: 目标坐标 [x_ratio, y_ratio]
            - message: 操作说明
            - confidence: 置信度
        """
        try:
            # 复制图像以避免修改原图
            image = screenshot.copy()
            
            # 添加辅助网格
            if use_grid:
                image = self._add_grid_overlay(image)
            
            # 转换图像为 Base64
            b64_img = self._image_to_base64(image)
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": instruction},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                ]}
            ]
            
            # 调用 API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,  # 降低随机性，提高稳定性
                max_tokens=500
            )
            
            # 解析响应
            content = response.choices[0].message.content
            result = self._parse_json_response(content)
            
            if result is None:
                print(f"AI 返回格式错误: {content}")
                return None
            
            # 保存调试快照
            if save_debug:
                self._save_debug_snapshot(screenshot, result)
            
            # 添加到历史记录
            self.history.append({
                "instruction": instruction,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            print(f"Doubao API 错误: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            连接是否成功
        """
        try:
            # 创建一个简单的测试图像
            test_image = Image.new('RGB', (100, 100), color='white')
            
            # 发送测试请求
            result = self.analyze(
                test_image,
                "这是一个测试，请返回 action='none' 和 message='连接成功'",
                save_debug=False
            )
            
            return result is not None and result.get("action") == "none"
            
        except Exception as e:
            print(f"连接测试失败: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    print("AI 大脑模块测试")
    print("请先在配置文件中设置 API Key 和 Endpoint ID")
    
    # 示例用法（需要配置 API Key）
    # brain = DoubaoBrain(api_key="your_api_key", endpoint_id="ep-xxxxx")
    # result = brain.analyze(screenshot, "请分析当前界面")
    # print(result)