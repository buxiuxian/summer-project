"""
单元测试配置和工具函数
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import asyncio
from typing import Dict, Any

# 测试配置
pytest_plugins = []

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def sample_user_prompt():
    """示例用户输入"""
    return "什么是机器学习？"

@pytest.fixture
def sample_file_paths():
    """示例文件路径列表"""
    return ["test_data/sample.pdf", "test_data/sample.txt"]

@pytest.fixture
def sample_session_id():
    """示例会话ID"""
    return "test-session-123"

@pytest.fixture
def sample_chat_history():
    """示例聊天历史"""
    return [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！我是RS Agent，很高兴为您服务。"}
    ]

class MockResponse:
    """模拟LLM响应"""
    def __init__(self, content: str):
        self.content = content

class MockLangChainClient:
    """模拟LangChain客户端"""
    def __init__(self):
        self.responses = {}
    
    def add_mock_response(self, prompt: str, response: str):
        """添加模拟响应"""
        self.responses[prompt] = response
    
    async def ainvoke(self, prompt, **kwargs):
        """异步调用模拟"""
        for prompt_key, response in self.responses.items():
            if prompt_key in prompt:
                return MockResponse(response)
        return MockResponse("这是一个模拟响应")
    
    async def generate_response(self, human_msg: str, system_msg: str = None):
        """生成响应模拟"""
        for prompt_key, response in self.responses.items():
            if prompt_key in human_msg:
                return response
        # 如果没有匹配到，但human_msg包含"关键词"，则返回第一个响应
        if "关键词" in human_msg and self.responses:
            return list(self.responses.values())[0]
        return "这是一个模拟响应"

@pytest.fixture
def mock_langchain_client():
    """模拟LangChain客户端fixture"""
    return MockLangChainClient()

# 测试工具函数
def create_test_files():
    """创建测试文件"""
    test_dir = Path("test_data")
    test_dir.mkdir(exist_ok=True)
    
    # 创建测试文本文件
    test_file = test_dir / "sample.txt"
    test_file.write_text("这是一个测试文件的内容。\n包含机器学习相关信息。")
    
    return test_file

def cleanup_test_files():
    """清理测试文件"""
    test_dir = Path("test_data")
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir)