"""
Agent配置模块 - 控制是否使用LangChain实现
"""

import os
from typing import Dict, Any

class AgentConfig:
    """Agent配置类"""
    
    def __init__(self):
        # 从环境变量读取配置，默认使用LangChain
        self.use_langchain = os.getenv("USE_LANGCHAIN", "true").lower() == "true"
        self.debug_mode = os.getenv("AGENT_DEBUG", "false").lower() == "true"
    
    def switch_to_langchain(self):
        """切换到LangChain实现"""
        self.use_langchain = True
        print("已切换到LangChain实现")
    
    def switch_to_native(self):
        """切换到原生实现"""
        self.use_langchain = False
        print("已切换到原生实现")
    
    def get_current_implementation(self) -> str:
        """获取当前使用的实现方式"""
        return "LangChain" if self.use_langchain else "原生"
    
    def is_langchain_enabled(self) -> bool:
        """检查是否启用LangChain"""
        return self.use_langchain
    
    def is_debug_enabled(self) -> bool:
        """检查是否启用调试模式"""
        return self.debug_mode

# 全局配置实例
agent_config = AgentConfig()

def get_agent_config() -> AgentConfig:
    """获取agent配置实例"""
    return agent_config

def set_use_langchain(enable: bool = True):
    """设置是否使用LangChain"""
    if enable:
        agent_config.switch_to_langchain()
    else:
        agent_config.switch_to_native()

def is_langchain_enabled() -> bool:
    """便捷函数：检查是否启用LangChain"""
    return agent_config.is_langchain_enabled()

def set_debug_mode(enable: bool = True):
    """设置调试模式"""
    agent_config.debug_mode = enable
    print(f"调试模式: {'启用' if enable else '禁用'}")

def print_config():
    """打印当前配置"""
    print(f"""
=== Agent配置信息 ===
实现方式: {agent_config.get_current_implementation()}
调试模式: {'启用' if agent_config.debug_mode else '禁用'}
LangChain状态: {'启用' if agent_config.use_langchain else '禁用'}
=====================
    """.strip()) 