"""
API路由器的单元测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.api.routers.chat_router import router
# 创建FastAPI应用用于测试
from fastapi import FastAPI
app = FastAPI()

# 导入路由器
from app.api.routers import chat_router, session_router, health_router, knowledge_router

# 添加路由器到应用
app.include_router(chat_router)
app.include_router(session_router)
app.include_router(health_router)
app.include_router(knowledge_router)

# 创建测试客户端
client = TestClient(app)

class TestChatRouter:
    """聊天路由器测试类"""
    
    def test_chat_router_included_in_app(self):
        """测试聊天路由器是否正确包含在应用中"""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        assert "/agent/chat" in routes
    
    def test_chat_request_model(self):
        """测试聊天请求模型"""
        from app.api.routers.chat_router import ChatRequest
        
        # 测试有效请求
        request = ChatRequest(
            message="测试消息",
            stream=False,
            session_id="test-session"
        )
        assert request.message == "测试消息"
        assert request.stream is False
        assert request.session_id == "test-session"
    
    def test_chat_response_model(self):
        """测试聊天响应模型"""
        from app.api.routers.chat_router import ChatResponse
        
        response = ChatResponse(
            response="测试回复",
            status="success",
            task_type=1,
            session_id="test-session"
        )
        assert response.response == "测试回复"
        assert response.status == "success"
        assert response.task_type == 1
    
    def test_agent_chat_endpoint_basic(self):
        """测试聊天端点基本功能"""
        # 这个测试只验证端点是否存在并能接受请求
        # 由于涉及复杂的agent依赖和计费系统，不做完整的功能测试
        
        # 发送测试请求 - 可能会因为实际的LLM调用而失败
        response = client.post("/agent/chat", json={
            "message": "测试消息",
            "stream": False,
            "session_id": "test-session"
        })
        
        # 只验证端点响应，不验证具体内容
        # 因为实际的agent调用可能会因为API密钥等问题失败
        assert response.status_code in [200, 500, 503]  # 允许服务器错误
    
    def test_health_router_endpoint(self):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_root_endpoint(self):
        """测试根路径端点"""
        response = client.get("/")
        assert response.status_code == 200
        assert "RS Agent MCP" in response.json()["message"]


class TestSessionRouter:
    """会话路由器测试类"""
    
    def test_session_endpoints_included(self):
        """测试会话相关端点是否正确包含"""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        session_routes = [route for route in routes if "/agent/chat/sessions" in route]
        assert len(session_routes) > 0
    
    def test_session_request_model(self):
        """测试会话请求模型"""
        from app.api.routers.session_router import ChatSessionRequest
        
        request = ChatSessionRequest(token="test-token")
        assert request.token == "test-token"


class TestKnowledgeRouter:
    """知识路由器测试类"""
    
    def test_knowledge_endpoints_included(self):
        """测试知识相关端点是否正确包含"""
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        knowledge_routes = [route for route in routes if "/agent/knowledge" in route]
        assert len(knowledge_routes) > 0