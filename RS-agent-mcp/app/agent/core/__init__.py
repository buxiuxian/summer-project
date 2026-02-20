"""
Agent核心模块
"""

from .agent_factory import agent_factory, AgentConfig, BaseAgent
from .agent_manager import agent_manager, AgentManager
from .langchain_agent_impl import LangChainAgent, langchain_agent_config
from .task_classifier import task_classifier, TaskClassifier
from .response_generator import response_generator, ResponseGenerator
from .agent_orchestrator import agent_orchestrator, AgentOrchestrator

# 保留原有的组件导入（如果存在）
try:
    from .agent_orchestrator import AgentOrchestrator
    from .task_classifier import TaskClassifier
    from .response_generator import ResponseGenerator
    __all__ = [
        "agent_factory",
        "AgentConfig", 
        "BaseAgent",
        "agent_manager",
        "AgentManager",
        "LangChainAgent",
        "langchain_agent_config",
        "task_classifier",
        "TaskClassifier",
        "response_generator", 
        "ResponseGenerator",
        "agent_orchestrator",
        "AgentOrchestrator"
    ]
except ImportError:
    __all__ = [
        "agent_factory",
        "AgentConfig", 
        "BaseAgent",
        "agent_manager",
        "AgentManager",
        "LangChainAgent",
        "langchain_agent_config",
        "task_classifier",
        "TaskClassifier",
        "response_generator", 
        "ResponseGenerator",
        "agent_orchestrator",
        "AgentOrchestrator"
    ]