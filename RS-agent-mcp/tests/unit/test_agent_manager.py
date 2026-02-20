"""
Agent管理器的单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from app.agent.core.agent_manager import AgentManager
from app.agent.core.agent_factory import AgentConfig


class TestAgentManager:
    """Agent管理器测试类"""
    
    @pytest.fixture
    def agent_manager(self):
        """创建Agent管理器实例"""
        return AgentManager()
    
    def test_agent_manager_initialization(self, agent_manager):
        """测试Agent管理器初始化"""
        assert agent_manager is not None
        assert hasattr(agent_manager, '_initialize_agents')
    
    @pytest.mark.asyncio
    async def test_run_agent_with_default_type(self, agent_manager):
        """测试使用默认Agent类型运行"""
        # Mock agent factory
        with patch('app.agent.core.agent_manager.agent_factory') as mock_factory:
            # 设置mock
            mock_agent = AsyncMock()
            mock_agent.run.return_value = "测试结果"
            mock_factory.create_agent.return_value = mock_agent
            mock_factory.find_agent_for_mode.return_value = None
            mock_factory.get_default_agent_type.return_value = "langchain"
            
            # 执行测试
            result = await agent_manager.run_agent(
                instruction_mode=0,
                user_prompt="测试问题"
            )
            
            # 验证结果
            assert result == "测试结果"
            mock_factory.create_agent.assert_called_once_with("langchain")
            mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_analysis_agent(self, agent_manager):
        """测试运行分析Agent"""
        with patch.object(agent_manager, 'run_agent', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = "分析结果"
            
            result = await agent_manager.run_analysis_agent(
                instruction_mode=1,
                user_prompt="分析这个问题"
            )
            
            assert result == "分析结果"
            mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_knowledge_query_with_sources(self, agent_manager):
        """测试运行知识查询Agent"""
        with patch.object(agent_manager, 'run_agent', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"answer": "答案", "sources": []}
            
            result = await agent_manager.run_knowledge_query_with_sources(
                user_prompt="知识查询"
            )
            
            assert isinstance(result, dict)
            assert "answer" in result
            mock_run.assert_called_once_with(
                instruction_mode=1,
                user_prompt="知识查询",
                file_paths=None,
                session_id=None,
                chat_history=None,
                return_structured=True
            )
    
    def test_get_available_agents(self, agent_manager):
        """测试获取可用Agent列表"""
        with patch('app.agent.core.agent_manager.agent_factory') as mock_factory:
            mock_factory.list_agent_types.return_value = ["langchain"]
            mock_factory.get_agent_config.return_value = AgentConfig(
                agent_type="langchain",
                name="LangChain Agent",
                description="基于LangChain的Agent",
                supported_modes=[-1, 0, 1, 2, 3]
            )
            
            result = agent_manager.get_available_agents()
            
            assert len(result) == 1
            assert result[0]["type"] == "langchain"
            assert result[0]["name"] == "LangChain Agent"
    
    def test_get_agent_info(self, agent_manager):
        """测试获取特定Agent信息"""
        with patch('app.agent.core.agent_manager.agent_factory') as mock_factory:
            mock_factory.get_agent_config.return_value = AgentConfig(
                agent_type="langchain",
                name="LangChain Agent",
                description="基于LangChain的Agent",
                supported_modes=[-1, 0, 1, 2, 3]
            )
            
            result = agent_manager.get_agent_info("langchain")
            
            assert result is not None
            assert result["type"] == "langchain"
            assert result["name"] == "LangChain Agent"
            
            # 测试不存在的Agent
            mock_factory.get_agent_config.return_value = None
            result = agent_manager.get_agent_info("nonexistent")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_run_agent_invalid_instruction_mode_type(self, agent_manager):
        """测试无效instruction_mode类型的处理"""
        with pytest.raises(ValueError) as exc_info:
            await agent_manager.run_agent(
                instruction_mode="invalid",  # 字符串而不是整数
                user_prompt="测试消息"
            )
        assert "instruction_mode必须是整数" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_agent_invalid_instruction_mode_value(self, agent_manager):
        """测试无效instruction_mode值的处理"""
        with pytest.raises(ValueError) as exc_info:
            await agent_manager.run_agent(
                instruction_mode=999,  # 不支持的值
                user_prompt="测试消息"
            )
        assert "不支持的指令模式" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_run_agent_valid_error_codes(self, agent_manager):
        """测试有效的错误代码处理"""
        # 应该允许错误代码通过验证
        with patch('app.agent.core.agent_manager.agent_factory') as mock_factory:
            mock_factory.find_agent_for_mode.return_value = None
            mock_factory.get_default_agent_type.return_value = "langchain"
            mock_factory.create_agent.return_value = Mock()
            mock_factory.create_agent.return_value.run = AsyncMock(return_value="test result")
            
            # 测试各种错误代码
            error_codes = [-100, -101, -102, -103]
            for error_code in error_codes:
                result = await agent_manager.run_agent(
                    instruction_mode=error_code,
                    user_prompt="测试消息"
                )
                assert result == "test result"