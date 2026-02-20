"""
LangChain Agent实现 - 基于Agent基类的具体实现
"""

import logging
from typing import List, Optional, Dict, Any, Union

from .agent_factory import BaseAgent, AgentConfig
from .agent_orchestrator import agent_orchestrator

logger = logging.getLogger(__name__)

class LangChainAgent(BaseAgent):
    """基于LangChain的Agent实现"""
    
    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.supported_modes = config.supported_modes
        
    def supports_mode(self, instruction_mode: int) -> bool:
        """检查是否支持指定的指令模式"""
        return instruction_mode in self.supported_modes
    
    async def run(
        self,
        instruction_mode: int,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Union[str, dict]:
        """运行Agent"""
        if not self.supports_mode(instruction_mode):
            raise ValueError(f"Agent类型 {self.agent_type} 不支持指令模式 {instruction_mode}")
        
        logger.info(f"运行LangChain Agent: mode={instruction_mode}, prompt={user_prompt[:50]}...")
        
        try:
            if instruction_mode == 1 and kwargs.get('return_structured', False):
                # 知识问答模式，返回结构化结果 - import here to avoid circular import
                from ..chains.knowledge_chain import run_knowledge_query_with_sources_structured
                return await run_knowledge_query_with_sources_structured(
                    user_prompt=user_prompt,
                    file_paths=file_paths,
                    session_id=session_id,
                    chat_history=chat_history
                )
            else:
                # 其他模式，返回字符串结果 - use orchestrator directly
                return await agent_orchestrator.process_task(
                    instruction_mode=instruction_mode,
                    user_prompt=user_prompt,
                    file_paths=file_paths,
                    output_path=output_path,
                    session_id=session_id,
                    rshub_token=rshub_token,
                    chat_history=chat_history
                )
        except Exception as e:
            logger.error(f"LangChain Agent运行失败: {str(e)}")
            raise

# 创建LangChain Agent的配置
langchain_agent_config = AgentConfig(
    agent_type="langchain",
    name="LangChain Agent",
    description="基于LangChain实现的多功能AI Agent",
    supported_modes=[-1, 0, 1, 2, 3]  # 支持所有模式
)