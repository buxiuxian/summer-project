"""
AI Agent核心逻辑 - 使用Agent管理器实现
重构后的Agent接口，支持多种Agent类型和工厂模式
"""

from typing import List, Optional, Dict, Any
import logging

# 导入Agent管理器
from .core.agent_manager import agent_manager

# 配置日志
logger = logging.getLogger(__name__)

async def run_analysis_agent(
    instruction_mode: int,
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    rshub_token: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    RS Agent的核心函数，根据不同的指令模式执行相应的任务
    使用Agent管理器实现，支持多种Agent类型
    
    Args:
        instruction_mode: 指令模式 (-1=通用回答, 0=任务分类, 1=知识问答, 2=参数构建环境, 3=环境推断参数)
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        output_path: 结果输出路径
        session_id: 会话ID
        rshub_token: RSHub token，用于建模任务
        chat_history: 会话历史消息列表
    
    Returns:
        处理结果字符串，如果失败返回错误信息
        
    错误代码说明：
        -1: 任务分类失败，进入通用回答模式
        -100: 用户主动中止请求
        -101: LLM调用超时
        -102: 网络连接错误
    """
    
    logger.info(f"使用Agent管理器运行分析任务: mode={instruction_mode}, prompt={user_prompt[:50]}...")
    
    return await agent_manager.run_analysis_agent(
        instruction_mode=instruction_mode,
        user_prompt=user_prompt,
        file_paths=file_paths,
        output_path=output_path,
        session_id=session_id,
        rshub_token=rshub_token,
        chat_history=chat_history
    )

async def run_knowledge_query_with_sources(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """
    增强的知识问答函数，返回带有文件源信息的结构化结果
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        session_id: 会话ID
        chat_history: 会话历史消息列表
    
    Returns:
        包含答案和源文件信息的字典
    """
    
    logger.info(f"使用Agent管理器运行知识查询: prompt={user_prompt[:50]}...")
    
    return await agent_manager.run_knowledge_query_with_sources(
        user_prompt=user_prompt,
        file_paths=file_paths,
        session_id=session_id,
        chat_history=chat_history
    )

# 便捷函数：获取可用Agent信息
def get_available_agents() -> List[Dict[str, Any]]:
    """
    获取所有可用的Agent信息
    
    Returns:
        Agent信息列表
    """
    return agent_manager.get_available_agents()

# 便捷函数：获取指定Agent信息
def get_agent_info(agent_type: str) -> Optional[Dict[str, Any]]:
    """
    获取指定Agent的信息
    
    Args:
        agent_type: Agent类型
        
    Returns:
        Agent信息字典，如果不存在返回None
    """
    return agent_manager.get_agent_info(agent_type)

# 便捷函数：设置默认Agent类型
def set_default_agent_type(agent_type: str):
    """
    设置默认Agent类型
    
    Args:
        agent_type: Agent类型
    """
    from .core.agent_factory import agent_factory
    agent_factory.set_default_agent_type(agent_type)

# 便捷函数：获取默认Agent类型
def get_default_agent_type() -> str:
    """
    获取默认Agent类型
    
    Returns:
        默认Agent类型
    """
    from .core.agent_factory import agent_factory
    return agent_factory.get_default_agent_type() 