"""
Agent配置管理器 - 管理不同类型Agent的配置和实例化
"""

from typing import Dict, Any, Optional, Type, Union
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class AgentConfig:
    """Agent配置基类"""
    
    def __init__(
        self,
        agent_type: str,
        name: str,
        description: str,
        supported_modes: list,
        **kwargs
    ):
        self.agent_type = agent_type
        self.name = name
        self.description = description
        self.supported_modes = supported_modes
        self.config = kwargs
        
    def get_config(self) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "supported_modes": self.supported_modes,
            **self.config
        }

class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_type = config.agent_type
        
    @abstractmethod
    async def run(
        self,
        instruction_mode: int,
        user_prompt: str,
        file_paths: Optional[list] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Union[str, dict]:
        """运行Agent"""
        pass
    
    @abstractmethod
    def supports_mode(self, instruction_mode: int) -> bool:
        """检查是否支持指定的指令模式"""
        pass

class AgentFactory:
    """Agent工厂类"""
    
    def __init__(self):
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._agent_classes: Dict[str, Type[BaseAgent]] = {}
        self._default_agent_type = "langchain"
        
    def register_agent(
        self,
        agent_type: str,
        agent_class: Type[BaseAgent],
        config: AgentConfig
    ):
        """注册Agent类型"""
        self._agent_configs[agent_type] = config
        self._agent_classes[agent_type] = agent_class
        logger.info(f"已注册Agent类型: {agent_type}")
        
    def create_agent(
        self,
        agent_type: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        """创建Agent实例"""
        if agent_type is None:
            agent_type = self._default_agent_type
            
        if agent_type not in self._agent_configs:
            raise ValueError(f"未知的Agent类型: {agent_type}")
            
        config = self._agent_configs[agent_type]
        agent_class = self._agent_classes[agent_type]
        
        # 应用配置覆盖
        if config_overrides:
            config_dict = config.get_config()
            config_dict.update(config_overrides)
            config = AgentConfig(**config_dict)
            
        return agent_class(config)
    
    def get_agent_config(self, agent_type: str) -> Optional[AgentConfig]:
        """获取Agent配置"""
        return self._agent_configs.get(agent_type)
    
    def list_agent_types(self) -> list:
        """列出所有可用的Agent类型"""
        return list(self._agent_configs.keys())
    
    def get_default_agent_type(self) -> str:
        """获取默认Agent类型"""
        return self._default_agent_type
    
    def set_default_agent_type(self, agent_type: str):
        """设置默认Agent类型"""
        if agent_type not in self._agent_configs:
            raise ValueError(f"未知的Agent类型: {agent_type}")
        self._default_agent_type = agent_type
        logger.info(f"默认Agent类型已设置为: {agent_type}")
    
    def supports_mode(self, agent_type: str, instruction_mode: int) -> bool:
        """检查Agent类型是否支持指定的指令模式"""
        if agent_type not in self._agent_configs:
            return False
        return instruction_mode in self._agent_configs[agent_type].supported_modes
    
    def find_agent_for_mode(self, instruction_mode: int) -> Optional[str]:
        """查找支持指定指令模式的Agent类型"""
        for agent_type, config in self._agent_configs.items():
            if instruction_mode in config.supported_modes:
                return agent_type
        return None

# 全局Agent工厂实例
agent_factory = AgentFactory()