# -*- coding: utf-8 -*-
"""
配置管理器
负责初始化 user_data/ 目录结构和管理配置文件
"""

import os
import json

class ConfigManager:
    def __init__(self):
        self.user_data_dir = "user_data"
        self.config_file = os.path.join(self.user_data_dir, "config.json")
        self._initialize()
    
    def _initialize(self):
        """初始化目录结构和配置文件"""
        # 创建 user_data 目录
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)
        
        # 创建配置文件模板
        if not os.path.exists(self.config_file):
            default_config = {
                "api_key": "",
                "endpoint_id": "",
                "selected_game": "",
                "selected_window": "",
                "click_delay": 0.5
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    def get_config(self):
        """获取完整配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {
                "api_key": "",
                "endpoint_id": "",
                "selected_game": "",
                "selected_window": "",
                "click_delay": 0.5
            }
    
    def save_config(self, config):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_api_key(self):
        """获取 API Key"""
        config = self.get_config()
        return config.get("api_key", "")
    
    def get_endpoint_id(self):
        """获取 Endpoint ID"""
        config = self.get_config()
        return config.get("endpoint_id", "")
    
    def get_user_data_path(self, filename):
        """获取 user_data 目录下的文件路径"""
        return os.path.join(self.user_data_dir, filename)

# 单例模式
config_manager = ConfigManager()
