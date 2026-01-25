import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), "user_data", "config.json")
        self.default_config = {
            "game": {
                "window_title": "",
                "resolution": "1920x1080"
            },
            "ai": {
                "api_key": "",
                "model": "doubao-pro",
                "temperature": 0.7
            },
            "debug": {
                "enabled": False,
                "log_level": "info"
            }
        }
    
    def _ensure_directory(self):
        """确保配置文件目录存在"""
        directory = os.path.dirname(self.config_path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _ensure_config(self):
        """确保配置文件存在，不存在则创建默认配置"""
        self._ensure_directory()
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        self._ensure_config()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            # 合并默认配置，确保所有必要的键存在
            return self._merge_configs(self.default_config, config)
        except Exception:
            return self.default_config
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            self._ensure_directory()
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的路径"""
        config = self.load_config()
        keys = key_path.split(".")
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any) -> bool:
        """设置配置值，支持点号分隔的路径"""
        config = self.load_config()
        keys = key_path.split(".")
        current = config
        
        # 导航到目标键的父级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置值
        current[keys[-1]] = value
        return self.save_config(config)
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和用户配置"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def reset(self) -> bool:
        """重置为默认配置"""
        return self.save_config(self.default_config)
