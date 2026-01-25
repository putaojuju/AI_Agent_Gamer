# -*- coding: utf-8 -*-
import json
import os
import logging

class ConfigManager:
    """
    配置管理器 - 隐私隔离增强版
    遵循规则: 用户数据强制存储在 user_data/ 目录下
    """
    def __init__(self):
        # 获取项目根目录
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 定义用户数据目录 (隐私隔离区)
        self.user_data_dir = os.path.join(self.root_dir, "user_data")
        self.config_path = os.path.join(self.user_data_dir, "config.json")
        
        # 默认配置模板
        self.default_config = {
            "game": {
                "window_title": "Arknights",
                "resolution": "1920x1080"
            },
            "ai": {
                "api_key": "",
                "endpoint_id": "",
                "model": "doubao-pro-4k",
                "temperature": 0.7
            },
            "debug": {
                "enabled": False,
                "log_level": "INFO"
            }
        }
        
        # 初始化：确保目录存在并加载配置
        self._ensure_user_data_dir()
        self._ensure_config_exists()

    def _ensure_user_data_dir(self):
        """确保 user_data 目录存在"""
        if not os.path.exists(self.user_data_dir):
            try:
                os.makedirs(self.user_data_dir)
                logging.info(f"已创建用户数据目录: {self.user_data_dir}")
            except Exception as e:
                logging.error(f"无法创建用户数据目录: {e}")

    def _ensure_config_exists(self):
        """确保配置文件存在，不存在则创建默认配置"""
        if not os.path.exists(self.config_path):
            self.save_config(self.default_config)

    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self.default_config

    def save_config(self, config_data):
        """保存配置"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"保存配置失败: {e}")
            return False

    def get(self, key_path, default=None):
        """获取配置值，支持 'ai.api_key' 格式"""
        config = self.load_config()
        keys = key_path.split(".")
        value = config
        try:
            for k in keys:
                value = value[k]
            # 增加环境变量覆盖
            env_key = key_path.upper().replace('.', '_') # 如 AI_API_KEY
            return os.environ.get(env_key, value)
        except (KeyError, TypeError):
            # 即使配置文件中不存在，也尝试从环境变量获取
            env_key = key_path.upper().replace('.', '_')
            return os.environ.get(env_key, default)

    def set(self, key_path, value):
        """设置配置值"""
        config = self.load_config()
        keys = key_path.split(".")
        current = config
        
        # 遍历到倒数第二层
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value
        return self.save_config(config)
    
    def get_user_data_path(self, filename):
        """获取 user_data 目录下文件的完整路径"""
        return os.path.join(self.user_data_dir, filename)