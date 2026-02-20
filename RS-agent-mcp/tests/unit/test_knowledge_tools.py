"""
知识工具的单元测试
"""

import pytest
from unittest.mock import Mock, patch

from app.agent.tools.knowledge_tools import KnowledgeTools


class TestKnowledgeTools:
    """知识工具测试类"""
    
    @pytest.fixture
    def knowledge_tools(self):
        """创建知识工具实例"""
        return KnowledgeTools()
    
    def test_parse_keywords_from_response_valid_format(self, knowledge_tools):
        """测试从有效格式响应中解析关键词"""
        response = '''关键词分析结果：
[(机器学习, 0.9), (算法, 0.7), (深度学习, 0.8)]
'''
        result = knowledge_tools._parse_keywords_from_response(response)
        
        assert len(result) == 3
        assert result[0]["keyword"] == "机器学习"
        # 权重会被归一化，所以检查比例而不是绝对值
        assert result[0]["weight"] > 0
    
    def test_parse_keywords_from_response_invalid_json(self, knowledge_tools):
        """测试从无效JSON响应中解析关键词"""
        response = "这是一个普通的回答，没有JSON格式"
        result = knowledge_tools._parse_keywords_from_response(response)
        
        assert result == []
    
    def test_extract_keywords_simple(self, knowledge_tools):
        """测试简单关键词提取"""
        user_prompt = "我想了解微波和遥感的区别"
        result = knowledge_tools._extract_keywords_simple(user_prompt)
        
        assert len(result) > 0
        # 应该包含微波遥感相关关键词
        keywords = [item["keyword"] for item in result]
        assert any("Microwave" in kw for kw in keywords) or any("Remote" in kw for kw in keywords)
    
    def test_extract_keywords_simple_empty(self, knowledge_tools):
        """测试空输入的关键词提取"""
        user_prompt = ""
        result = knowledge_tools._extract_keywords_simple(user_prompt)
        
        assert result == []
    
    def test_get_file_info_string_with_files(self, knowledge_tools):
        """测试获取文件信息字符串（有文件）"""
        # 创建测试文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f1:
            f1.write("test content")
            pdf_path = f1.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f2:
            f2.write("example content")
            txt_path = f2.name
        
        try:
            file_paths = [pdf_path, txt_path]
            result = knowledge_tools._get_file_info_string(file_paths)
            
            assert os.path.basename(pdf_path) in result
            assert os.path.basename(txt_path) in result
            assert "bytes" in result
        finally:
            # 清理测试文件
            os.unlink(pdf_path)
            os.unlink(txt_path)
    
    def test_get_file_info_string_no_files(self, knowledge_tools):
        """测试获取文件信息字符串（无文件）"""
        file_paths = None
        result = knowledge_tools._get_file_info_string(file_paths)
        
        assert result == ""
    
    def test_get_file_info_string_empty_list(self, knowledge_tools):
        """测试获取文件信息字符串（空列表）"""
        file_paths = []
        result = knowledge_tools._get_file_info_string(file_paths)
        
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_extract_keywords_with_llm(self, knowledge_tools, mock_langchain_client):
        """测试使用LLM提取关键词"""
        # 设置模拟响应 - 使用正确的格式
        mock_response = '''关键词提取结果：
[(机器学习, 0.9), (深度学习, 0.8)]'''
        mock_langchain_client.add_mock_response("提取关键词", mock_response)
        
        with patch('app.agent.tools.knowledge_tools.get_langchain_client', return_value=mock_langchain_client):
            result = await knowledge_tools.extract_keywords(
                user_prompt="机器学习和深度学习的区别",
                file_paths=None
            )
            
            assert len(result) == 2
            assert result[0]["keyword"] == "机器学习"
    
    @pytest.mark.asyncio
    async def test_extract_keywords_fallback_to_simple(self, knowledge_tools):
        """测试LLM失败时回退到简单提取"""
        with patch('app.agent.tools.knowledge_tools.get_langchain_client') as mock_client:
            # 模拟LLM调用失败
            mock_client.return_value.generate_response.side_effect = Exception("LLM调用失败")
            
            result = await knowledge_tools.extract_keywords(
                user_prompt="机器学习和深度学习",
                file_paths=None
            )
            
            assert len(result) > 0
            # 应该回退到简单关键词提取，由于输入中没有匹配的关键词，应该返回默认的英文关键词
            keywords = [item["keyword"] for item in result]
            assert any("Microwave" in kw or "Parameter" in kw for kw in keywords)