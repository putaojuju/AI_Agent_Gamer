import base64
import traceback
from typing import Dict, Any, Optional
from config_manager import ConfigManager

class AIBrain:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.api_key = self.config_manager.get("ai.api_key", "")
        self.model = self.config_manager.get("ai.model", "doubao-pro")
        self.temperature = self.config_manager.get("ai.temperature", 0.7)
        self.endpoint_id = self.config_manager.get("ai.endpoint_id", "")
    
    def _get_openai_client(self):
        """获取OpenAI兼容客户端"""
        try:
            from openai import OpenAI
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://ark.cn-beijing.volces.com/api/v3"
            )
            return client
        except Exception as e:
            return None
    
    def analyze(self, image_base64: str, system_prompt: str = "") -> Dict[str, Any]:
        """分析图像和提示，返回AI分析结果
        
        Args:
            image_base64: Base64编码的图像数据
            system_prompt: 系统提示
            
        Returns:
            包含分析结果的字典，包括raw_response字段
        """
        try:
            client = self._get_openai_client()
            if not client:
                return {
                    "success": False,
                    "data": None,
                    "raw_response": None,
                    "error": "无法初始化AI客户端",
                    "traceback": traceback.format_exc()
                }
            
            # 构建系统提示
            default_system_prompt = "你是一个二次元手游辅助AI，擅长分析游戏界面并提供操作建议。请详细分析画面内容，识别关键元素，并给出具体的行动建议。"
            final_system_prompt = system_prompt or default_system_prompt
            
            # 构建消息
            messages = [
                {"role": "system", "content": final_system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请分析当前游戏画面，识别关键元素，并提供操作建议。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # 调用AI API
            response = client.chat.completions.create(
                model=self.endpoint_id or "ep-20240125173242-2m2qh",
                messages=messages,
                temperature=self.temperature,
                max_tokens=2000
            )
            
            # 获取响应内容
            response_content = response.choices[0].message.content
            
            # 构建原始响应
            raw_response = {
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "content": response_content
            }
            
            # 构建返回结果
            result = {
                "success": True,
                "data": {
                    "analysis": response_content,
                    "usage": raw_response["usage"]
                },
                "raw_response": raw_response,
                "error": None
            }
            
            return result
        except Exception as e:
            # 捕获异常并包含traceback
            error_traceback = traceback.format_exc()
            return {
                "success": False,
                "data": None,
                "raw_response": None,
                "error": str(e),
                "traceback": error_traceback
            }
    
    def get_advice(self, context: str) -> Dict[str, Any]:
        """获取AI建议"""
        try:
            client = self._get_openai_client()
            if not client:
                return {
                    "success": False,
                    "data": None,
                    "raw_response": None,
                    "error": "无法初始化AI客户端",
                    "traceback": traceback.format_exc()
                }
            
            # 构建消息
            messages = [
                {"role": "system", "content": "你是一个游戏辅助AI，根据上下文提供详细的操作建议。"},
                {"role": "user", "content": context}
            ]
            
            # 调用AI API
            response = client.chat.completions.create(
                model=self.endpoint_id or "ep-20240125173242-2m2qh",
                messages=messages,
                temperature=self.temperature,
                max_tokens=1000
            )
            
            # 获取响应内容
            response_content = response.choices[0].message.content
            
            # 构建原始响应
            raw_response = {
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "content": response_content
            }
            
            return {
                "success": True,
                "data": {
                    "advice": response_content
                },
                "raw_response": raw_response,
                "error": None
            }
        except Exception as e:
            error_traceback = traceback.format_exc()
            return {
                "success": False,
                "data": None,
                "raw_response": None,
                "error": str(e),
                "traceback": error_traceback
            }
    
    def update_config(self):
        """更新配置"""
        self.api_key = self.config_manager.get("ai.api_key", "")
        self.model = self.config_manager.get("ai.model", "doubao-pro")
        self.temperature = self.config_manager.get("ai.temperature", 0.7)
        self.endpoint_id = self.config_manager.get("ai.endpoint_id", "")
