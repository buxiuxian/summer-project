
"""
任务分类器的单元测试
"""

import pytest
from unittest.mock import Mock, patch

from app.agent.core.task_classifier import TaskClassifier


class TestTaskClassifier:
    """任务分类器测试类"""
    
    @pytest.fixture
    def task_classifier(self):
        """创建任务分类器实例"""
        return TaskClassifier()
    
    def test_extract_task_type_from_response_valid_number(self, task_classifier):
        """测试从有效响应中提取任务类型"""
        response = "根据分析，这是一个任务类型为 1 的问题"
        result = task_classifier._extract_task_type_from_response(response)
        assert result == 1
    
    def test_extract_task_type_from_response_invalid_number(self, task_classifier):
        """测试从无效响应中提取任务类型"""
        response = "这是一个普通的问题，没有明确的任务类型"
        result = task_classifier._extract_task_type_from_response(response)
        assert result == 1  # 默认返回知识问答
    
    def test_extract_task_type_from_response_multiple_numbers(self, task_classifier):
        """测试从包含多个数字的响应中提取任务类型"""
        response = "经过分析，有2个可能的解决方案，建议使用方法1"
        result = task_classifier._extract_task_type_from_response(response)
        assert result == 1
    
    def test_classify_by_keywords_knowledge_query(self, task_classifier):
        """测试基于关键词的知识查询分类"""
        user_prompt = "什么是机器学习？请解释一下"
        result = task_classifier._classify_by_keywords(user_prompt)
        assert result == 1  # 知识问答
    
    def test_classify_by_keywords_general(self, task_classifier):
        """测试基于关键词的通用回答分类"""
        user_prompt = "你好，今天天气怎么样？"
        result = task_classifier._classify_by_keywords(user_prompt)
        assert result == 1  # 默认返回知识问答
    
    def test_classify_by_keywords_rshub_task(self, task_classifier):
        """测试基于关键词的RSHub任务分类"""
        user_prompt = "我需要构建一个土壤侵蚀模型"
        result = task_classifier._classify_by_keywords(user_prompt)
        assert result in [2, 3]  # RSHub相关任务
    
    def test_classify_by_keywords_empty_prompt(self, task_classifier):
        """测试空输入的分类"""
        user_prompt = ""
        result = task_classifier._classify_by_keywords(user_prompt)
        assert result == 1  # 默认返回知识问答
    
    @pytest.mark.asyncio
    async def test_classify_task_with_llm(self, task_classifier, mock_langchain_client):
        """测试使用LLM进行任务分类"""
        # 设置模拟响应
        mock_langchain_client.add_mock_response(
            "分析以下用户输入的任务类型",
            "根据分析，这是一个任务类型为 1 的问题"
        )
        
        with patch('app.agent.core.task_classifier.get_langchain_client', return_value=mock_langchain_client):
            result = await task_classifier.classify_task(
                user_prompt="什么是机器学习？",
                file_paths=None,
                chat_history=None
            )
            
            assert result == 1
    
    @pytest.mark.asyncio
    async def test_classify_task_fallback_to_keywords(self, task_classifier):
        """测试LLM失败时回退到关键词分类"""
        with patch('app.agent.core.task_classifier.get_langchain_client') as mock_client:
            # 模拟LLM调用失败
            mock_client.return_value.generate_response.side_effect = Exception("LLM调用失败")
            
            result = await task_classifier.classify_task(
                user_prompt="什么是机器学习？",
                file_paths=None,
                chat_history=None
            )
            
            assert result == 1  # 回退到关键词分类，"什么是机器学习"匹配知识问答关键词
    
    @pytest.mark.asyncio
    async def test_classify_task_api_error(self, task_classifier):
        """测试API认证错误处理"""
        with patch('app.agent.core.task_classifier.get_langchain_client') as mock_client:
            # 模拟API认证失败
            mock_client.return_value.generate_response.side_effect = Exception("Error code: 403 - {'error': {'code': 'AccountOverdueError'}}")
    
            result = await task_classifier.classify_task(
                user_prompt="测试API错误",
                file_paths=None,
                chat_history=None
            )
    
            assert result == -103  # API认证或余额问题
    
    def test_extract_task_type_from_response_error_detection(self, task_classifier):
        """测试错误信息检测功能"""
        # 测试各种错误信息格式
        error_responses = [
            "Error code: 403 - {'error': {'code': 'AccountOverdueError'}}",
            "抱歉，对话完成时出现问题: Error code: 403",
            "API Error: 500 Internal Server Error",
            "请求失败: Forbidden",
            "Rate limit exceeded"
        ]
        
        for error_response in error_responses:
            result = task_classifier._extract_task_type_from_response(error_response)
            assert result == -1  # 应该检测到错误信息并返回通用回答
    
    def test_extract_task_type_from_response_valid_with_error_keywords(self, task_classifier):
        """测试包含错误关键词的有效响应"""
        # 包含错误关键词但实际是有效讨论的响应
        valid_response = "什么是404错误？在网站开发中，404错误表示页面未找到。"
        result = task_classifier._extract_task_type_from_response(valid_response)
        assert result == 1  # 应该识别为知识问答