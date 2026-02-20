"""
Agent管理器 - 统一管理和调度所有Agent
重构后新增的组件，提供Agent工厂模式和管理功能
支持多种Agent类型的动态注册、创建和调度
保持向后兼容性，同时提供扩展性
"""

import logging
from typing import List, Optional, Dict, Any, Union

from .agent_factory import agent_factory, AgentConfig
from .langchain_agent_impl import LangChainAgent, langchain_agent_config

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent管理器"""
    
    def __init__(self):
        self._initialize_agents()
        
    def _initialize_agents(self):
        """初始化所有Agent"""
        # 注册LangChain Agent
        agent_factory.register_agent(
            agent_type="langchain",
            agent_class=LangChainAgent,
            config=langchain_agent_config
        )
        
        logger.info("Agent管理器初始化完成")
        
    async def run_agent(
        self,
        instruction_mode: int,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        agent_type: Optional[str] = None,
        return_structured: bool = False,
        **kwargs
    ) -> Union[str, dict]:
        """运行Agent"""
        
        # 验证instruction_mode的有效性
        if not isinstance(instruction_mode, int):
            logger.error(f"无效的instruction_mode类型: {type(instruction_mode)}, 值: {instruction_mode}")
            raise ValueError(f"instruction_mode必须是整数，当前为: {type(instruction_mode)}")
        
        # 检查instruction_mode是否在合理范围内
        valid_modes = [-1, 0, 1, 2, 3]  # 支持的模式和错误代码
        if instruction_mode not in valid_modes and not (instruction_mode <= -100 and instruction_mode >= -103):
            logger.error(f"无效的instruction_mode: {instruction_mode}")
            raise ValueError(f"不支持的指令模式: {instruction_mode}")
        
        # 如果未指定Agent类型，查找支持当前模式的Agent
        if agent_type is None:
            agent_type = agent_factory.find_agent_for_mode(instruction_mode)
            if agent_type is None:
                # 如果没有找到专门支持该模式的Agent，使用默认Agent
                agent_type = agent_factory.get_default_agent_type()
                
        logger.info(f"选择Agent类型: {agent_type}, 模式: {instruction_mode}")
        
        # 创建Agent实例
        try:
            agent = agent_factory.create_agent(agent_type)
        except ValueError as e:
            logger.error(f"创建Agent失败: {str(e)}")
            raise
        
        # 运行Agent
        return await agent.run(
            instruction_mode=instruction_mode,
            user_prompt=user_prompt,
            file_paths=file_paths,
            output_path=output_path,
            session_id=session_id,
            rshub_token=rshub_token,
            chat_history=chat_history,
            return_structured=return_structured,
            **kwargs
        )
    
    async def run_analysis_agent(
        self,
        instruction_mode: int,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """运行分析Agent - 兼容原始接口"""
        result = await self.run_agent(
            instruction_mode=instruction_mode,
            user_prompt=user_prompt,
            file_paths=file_paths,
            output_path=output_path,
            session_id=session_id,
            rshub_token=rshub_token,
            chat_history=chat_history
        )
        
        # 确保返回字符串
        if isinstance(result, dict):
            return str(result)
        return result
    
    async def run_knowledge_query_with_sources(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> dict:
        """运行知识查询Agent - 返回结构化结果"""
        return await self.run_agent(
            instruction_mode=1,
            user_prompt=user_prompt,
            file_paths=file_paths,
            session_id=session_id,
            chat_history=chat_history,
            return_structured=True
        )
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """获取所有可用的Agent信息"""
        agents_info = []
        for agent_type in agent_factory.list_agent_types():
            config = agent_factory.get_agent_config(agent_type)
            if config:
                agents_info.append({
                    "type": config.agent_type,
                    "name": config.name,
                    "description": config.description,
                    "supported_modes": config.supported_modes
                })
        return agents_info
    
    def get_agent_info(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """获取指定Agent的信息"""
        config = agent_factory.get_agent_config(agent_type)
        if config:
            return {
                "type": config.agent_type,
                "name": config.name,
                "description": config.description,
                "supported_modes": config.supported_modes
            }
        return None

# 全局Agent管理器实例
agent_manager = AgentManager()