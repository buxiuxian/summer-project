"""
基于LangChain的AI Agent核心逻辑 - 重构后的轻量级协调器
从原来的979行巨型文件重构为114行的协调器，减少88%的代码量
使用模块化组件：任务分类器、响应生成器、Agent编排器、知识工具等
"""

import logging
from typing import List, Optional, Dict, Any

# 导入新的模块化组件
from .core.agent_orchestrator import agent_orchestrator
from .chains.knowledge_chain import run_knowledge_query_with_sources_structured

# 配置日志
logger = logging.getLogger(__name__)

async def run_analysis_agent_langchain(
    instruction_mode: int,
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    rshub_token: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    基于LangChain的RS Agent核心函数，重构后使用模块化组件
    
    Args:
        instruction_mode: 指令模式 (-1=通用回答, 0=任务分类, 1=知识问答, 2=提交RSHub建模任务, 3=获取RSHub任务结果)
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        output_path: 结果输出路径
        session_id: 会话ID，用于进度回报和中止控制
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
    
    # 使用Agent编排器处理任务
    return await agent_orchestrator.process_task(
        instruction_mode=instruction_mode,
        user_prompt=user_prompt,
        file_paths=file_paths,
        output_path=output_path,
        session_id=session_id,
        rshub_token=rshub_token,
        chat_history=chat_history
    )

async def run_knowledge_query_with_sources_langchain(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """
    增强的知识问答函数，返回带有文件源信息的结构化结果
    重构后使用模块化的知识查询链
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        session_id: 会话ID
        chat_history: 会话历史消息列表
    
    Returns:
        包含答案和源文件信息的字典
    """
    
    logger.info("使用重构后的知识查询链处理增强知识问答...")
    
    return await run_knowledge_query_with_sources_structured(
        user_prompt=user_prompt,
        file_paths=file_paths,
        session_id=session_id,
        chat_history=chat_history
    )

# === 为了向后兼容，保留的辅助函数 ===
# 这些函数现在委托给相应的模块化组件

def _extract_task_type_from_response(response: str) -> int:
    """从LLM响应中提取任务类型编号 - 委托给任务分类器"""
    from .core.task_classifier import task_classifier
    return task_classifier._extract_task_type_from_response(response)

def _classify_by_keywords(user_prompt: str) -> int:
    """基于关键词的简单任务分类 - 委托给任务分类器"""
    from .core.task_classifier import task_classifier
    return task_classifier._classify_by_keywords(user_prompt)

def _parse_keywords_from_response(response: str) -> List[Dict[str, Any]]:
    """从LLM响应中解析关键词和权重 - 委托给知识工具"""
    from .tools.knowledge_tools import knowledge_tools
    return knowledge_tools._parse_keywords_from_response(response)

def _extract_keywords_simple(user_prompt: str) -> List[Dict[str, Any]]:
    """简单的关键词提取 - 委托给知识工具"""
    from .tools.knowledge_tools import knowledge_tools
    return knowledge_tools._extract_keywords_simple(user_prompt)

def _get_file_info_string(file_paths: Optional[List[str]]) -> str:
    """获取文件信息字符串 - 委托给知识工具"""
    from .tools.knowledge_tools import knowledge_tools
    return knowledge_tools._get_file_info_string(file_paths)