# -*- coding: utf-8 -*-
"""
Agent 核心模块
基于 ReAct 架构的游戏自动化 Agent
"""

import os
from typing import Optional, Dict, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub
import logging

log_dir = "log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'agent_core.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('agent_core')


class GameAgent:
    """
    游戏代理类，实现 ReAct 循环
    """
    
    def __init__(self, game_name: str, api_key: str, endpoint_id: str, base_url: str = "https://ark.cn-beijing.volces.com/api/v3"):
        """
        初始化游戏代理
        
        Args:
            game_name: 游戏名称（对应 knowledge/ 下的 JSON 文件名）
            api_key: 火山引擎 API Key
            endpoint_id: 豆包模型端点 ID
            base_url: API 基础 URL
        """
        self.game_name = game_name
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.base_url = base_url
        
        # 加载知识库
        from knowledge_manager import KnowledgeBase
        self.knowledge = KnowledgeBase()
        self.knowledge.load_game(game_name)
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=endpoint_id,
            temperature=0.3
        )
        
        # 加载工具
        from skills_registry import get_all_tools
        self.tools = get_all_tools()
        
        # 初始化视觉核心
        from vision_core import VisionCore
        self.vision = VisionCore()
        
        # 创建 Agent
        self._create_agent()
        
        logger.info(f"游戏代理初始化完成，游戏: {game_name}")
    
    def _create_agent(self):
        """
        创建 ReAct Agent
        """
        try:
            # 加载 ReAct 提示模板
            prompt = hub.pull("hwchase17/react")
            
            # 自定义系统提示
            system_prompt = f"""你是一个专业的游戏自动化助手，专门负责 {self.game_name} 游戏的自动化操作。

你有以下工具可以使用：
- click_text: 使用 OCR 查找并点击指定文字
- click_grid_coordinate: 点击指定网格坐标
- key_press: 按下并释放指定按键
- wait: 等待指定时间

游戏知识库：
{self._format_knowledge()}

操作原则：
1. 优先使用 OCR 文字定位，如果找不到文字再使用网格坐标
2. 每次操作后都要观察结果，根据结果决定下一步
3. 如果遇到未知情况，可以询问用户
4. 坐标操作优先使用文字锚点，其次使用网格坐标
5. 严禁使用硬编码的 time.sleep，必须使用视觉反馈验证

请按照以下格式思考和行动：
Thought: 思考当前情况和需要做什么
Action: 选择一个工具
Action Input: 工具的输入参数
Observation: 工具执行的结果
... (重复 Thought/Action/Action Input/Observation)
Thought: 我现在知道最终答案了
Final Answer: 最终答案

开始！
"""
            
            # 更新提示模板
            prompt.template = system_prompt
            
            # 创建 Agent
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # 创建 Agent 执行器
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10
            )
            
            logger.info("ReAct Agent 创建成功")
            
        except Exception as e:
            logger.error(f"创建 Agent 失败: {e}")
            raise
    
    def _format_knowledge(self) -> str:
        """
        格式化知识库为字符串
        
        Returns:
            知识库字符串
        """
        keys = self.knowledge.get_all_keys()
        knowledge_str = ""
        for key in keys:
            value = self.knowledge.query(key)
            knowledge_str += f"- {key}: {value}\n"
        return knowledge_str
    
    def run(self, instruction: str) -> str:
        """
        执行用户指令
        
        Args:
            instruction: 用户指令
        
        Returns:
            执行结果
        """
        try:
            logger.info(f"开始执行指令: {instruction}")
            
            # 获取当前截图
            base64_img, pil_img, grid_map = self.vision.get_annotated_screenshot()
            
            if base64_img is None:
                return "截图失败，无法继续执行"
            
            # 构建完整的指令，包含截图信息
            full_instruction = f"""当前游戏: {self.game_name}

用户指令: {instruction}

当前截图已添加 4x4 网格标注，请使用网格坐标辅助定位。
"""
            
            # 执行 Agent
            result = self.agent_executor.invoke({"input": full_instruction})
            
            logger.info(f"指令执行完成: {result}")
            return result.get("output", "执行完成")
            
        except Exception as e:
            logger.error(f"执行指令失败: {e}")
            return f"执行失败: {str(e)}"
    
    def run_sequence(self, instructions: List[str]) -> List[str]:
        """
        执行指令序列
        
        Args:
            instructions: 指令列表
        
        Returns:
            结果列表
        """
        results = []
        for i, instruction in enumerate(instructions, 1):
            logger.info(f"执行第 {i}/{len(instructions)} 步: {instruction}")
            result = self.run(instruction)
            results.append(result)
            
            # 如果执行失败，中断
            if "失败" in result or "错误" in result:
                logger.warning(f"第 {i} 步执行失败，中断执行")
                break
        
        return results
    
    def query_knowledge(self, question: str) -> Optional[str]:
        """
        查询知识库
        
        Args:
            question: 查询问题
        
        Returns:
            查询结果
        """
        return self.knowledge.query(question)
    
    def add_knowledge(self, key: str, value: str) -> bool:
        """
        添加知识到当前游戏知识库
        
        Args:
            key: 知识键
            value: 知识值
        
        Returns:
            是否添加成功
        """
        return self.knowledge.add_knowledge(key, value)
    
    def save_knowledge(self) -> bool:
        """
        保存当前游戏知识库
        
        Returns:
            是否保存成功
        """
        return self.knowledge.save_current_game()


if __name__ == "__main__":
    print("Agent 核心模块测试")
    print("使用示例:")
    print("""
    from agent_core import GameAgent
    
    # 创建游戏代理
    agent = GameAgent(
        game_name="arknights",
        api_key="your_api_key",
        endpoint_id="ep-xxxxx"
    )
    
    # 执行指令
    result = agent.run("点击作战按钮")
    print(result)
    
    # 查询知识库
    knowledge = agent.query_knowledge("龙门币")
    print(knowledge)
    """)
