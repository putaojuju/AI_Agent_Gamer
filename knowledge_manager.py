# -*- coding: utf-8 -*-
"""
知识库管理模块
负责加载和查询不同游戏的知识库
"""

import json
import os
from typing import Dict, Optional, List
import logging

log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'knowledge_manager.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('knowledge_manager')


class KnowledgeBase:
    """
    知识库类，管理游戏相关的知识和规则
    """
    
    def __init__(self, knowledge_dir: str = "knowledge"):
        """
        初始化知识库
        
        Args:
            knowledge_dir: 知识库目录路径
        """
        self.knowledge_dir = knowledge_dir
        self.current_game = None
        self.current_data = {}
        logger.info(f"知识库管理器初始化完成，知识库目录: {knowledge_dir}")
    
    def list_games(self) -> List[str]:
        """
        列出所有可用的游戏
        
        Returns:
            游戏名称列表
        """
        try:
            if not os.path.exists(self.knowledge_dir):
                return []
            
            games = []
            for filename in os.listdir(self.knowledge_dir):
                if filename.endswith('.json'):
                    game_name = filename[:-5]
                    games.append(game_name)
            
            logger.info(f"可用游戏列表: {games}")
            return games
            
        except Exception as e:
            logger.error(f"列出游戏失败: {e}")
            return []
    
    def load_game(self, game_name: str) -> bool:
        """
        加载指定游戏的知识库
        
        Args:
            game_name: 游戏名称（不含 .json 后缀）
        
        Returns:
            是否加载成功
        """
        try:
            # 修复路径遍历风险
            game_name = os.path.basename(game_name) # 去除路径
            filepath = os.path.join(self.knowledge_dir, f"{game_name}.json")
            
            if not os.path.exists(filepath):
                logger.error(f"知识库文件不存在: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                self.current_data = json.load(f)
                self.current_game = game_name
            
            logger.info(f"成功加载游戏知识库: {game_name}，包含 {len(self.current_data)} 条知识")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"知识库 JSON 格式错误: {e}")
            return False
        except Exception as e:
            logger.error(f"加载知识库失败: {e}")
            return False
    
    def query(self, question: str) -> Optional[str]:
        """
        在当前加载的知识库中查询信息
        
        Args:
            question: 查询问题或关键词
        
        Returns:
            查询结果，未找到返回 None
        """
        if not self.current_game:
            logger.warning("未加载任何游戏知识库")
            return None
        
        try:
            # 精确匹配
            if question in self.current_data:
                result = self.current_data[question]
                logger.info(f"精确匹配查询: '{question}' -> '{result}'")
                return result
            
            # 模糊匹配（检查问题是否包含某个键）
            for key, value in self.current_data.items():
                if question in key or key in question:
                    logger.info(f"模糊匹配查询: '{question}' -> '{key}' -> '{value}'")
                    return value
            
            # 检查值中是否包含问题
            for key, value in self.current_data.items():
                if question in str(value):
                    logger.info(f"值匹配查询: '{question}' -> '{key}' -> '{value}'")
                    return value
            
            logger.debug(f"未找到匹配的知识: '{question}'")
            return None
            
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return None
    
    def get_all_keys(self) -> List[str]:
        """
        获取当前知识库的所有键
        
        Returns:
            键列表
        """
        if not self.current_game:
            return []
        
        return list(self.current_data.keys())
    
    def add_knowledge(self, key: str, value: str) -> bool:
        """
        向当前知识库添加知识
        
        Args:
            key: 知识键
            value: 知识值
        
        Returns:
            是否添加成功
        """
        if not self.current_game:
            logger.warning("未加载任何游戏知识库")
            return False
        
        try:
            self.current_data[key] = value
            logger.info(f"添加知识: '{key}' -> '{value}'")
            return True
        except Exception as e:
            logger.error(f"添加知识失败: {e}")
            return False
    
    def save_current_game(self) -> bool:
        """
        保存当前游戏的知识库到文件
        
        Returns:
            是否保存成功
        """
        if not self.current_game:
            logger.warning("未加载任何游戏知识库")
            return False
        
        try:
            filepath = os.path.join(self.knowledge_dir, f"{self.current_game}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.current_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"知识库已保存: {filepath}")
            return True
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
            return False
    
    def get_current_game(self) -> Optional[str]:
        """
        获取当前加载的游戏名称
        
        Returns:
            游戏名称，未加载返回 None
        """
        return self.current_game


if __name__ == "__main__":
    print("知识库管理模块测试")
    print("使用示例:")
    print("""
    from knowledge_manager import KnowledgeBase
    
    # 创建知识库实例
    kb = KnowledgeBase()
    
    # 列出可用游戏
    games = kb.list_games()
    print(f"可用游戏: {games}")
    
    # 加载游戏知识库
    kb.load_game("arknights")
    
    # 查询信息
    result = kb.query("龙门币")
    print(f"查询结果: {result}")
    
    # 获取所有键
    keys = kb.get_all_keys()
    print(f"所有知识键: {keys}")
    """)
