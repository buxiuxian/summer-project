"""
会话管理路由器
处理所有会话相关的API端点
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging

from ...services.auth.auth_service import get_auth_service
from ...services.session.chat_service import get_chat_session_service

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 请求模型
class ChatSessionRequest(BaseModel):
    token: str
    chat_id: Optional[str] = None

class ChatSessionResponse(BaseModel):
    success: bool
    error: Optional[str] = None
    sessions: Optional[List[dict]] = None
    session_data: Optional[dict] = None
    chat_id: Optional[str] = None
    chat_title: Optional[str] = None

class DeleteChatRequest(BaseModel):
    chat_id: str

class DeleteChatResponse(BaseModel):
    success: bool
    error: Optional[str] = None

@router.post("/agent/chat/sessions", response_model=ChatSessionResponse)
async def list_chat_sessions(request: ChatSessionRequest):
    """
    获取用户的会话列表
    
    Args:
        request: 包含用户token的请求
    
    Returns:
        包含会话列表的响应
    """
    try:
        # 获取认证服务和会话服务
        auth_service = get_auth_service()
        chat_session_service = get_chat_session_service()
        
        # 验证token
        try:
            rshub_token = auth_service.get_rshub_token(request.token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # 获取会话列表
        sessions = await chat_session_service.list_sessions(rshub_token)
        
        logger.info(f"获取用户会话列表成功，共 {len(sessions)} 个会话")
        
        return ChatSessionResponse(
            success=True,
            sessions=sessions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        return ChatSessionResponse(
            success=False,
            error=str(e)
        )

@router.post("/agent/chat/sessions/{chat_id}", response_model=ChatSessionResponse)
async def get_chat_session(chat_id: str, request: ChatSessionRequest):
    """
    获取特定会话的详细信息
    
    Args:
        chat_id: 会话ID
        request: 包含用户token的请求
    
    Returns:
        包含会话详细信息的响应
    """
    try:
        # 获取认证服务和会话服务
        auth_service = get_auth_service()
        chat_session_service = get_chat_session_service()
        
        # 验证token
        try:
            rshub_token = auth_service.get_rshub_token(request.token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # 获取会话数据
        session_data = await chat_session_service.load_session(rshub_token, chat_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")
        
        logger.info(f"获取会话 {chat_id} 详情成功")
        
        return ChatSessionResponse(
            success=True,
            session_data=session_data,
            chat_id=chat_id,
            chat_title=session_data.get("title", "未命名会话")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话详情失败: {str(e)}")
        return ChatSessionResponse(
            success=False,
            error=str(e)
        )

@router.delete("/agent/chat/sessions/{chat_id}", response_model=DeleteChatResponse)
async def delete_chat_session(chat_id: str):
    """
    删除指定的会话
    
    Args:
        chat_id: 会话ID
    
    Returns:
        删除结果
    """
    try:
        # 获取会话服务
        chat_session_service = get_chat_session_service()
        
        # 删除会话
        result = await chat_session_service.delete_session(chat_id)
        
        if result.get("success"):
            logger.info(f"删除会话 {chat_id} 成功")
            return DeleteChatResponse(success=True)
        else:
            logger.error(f"删除会话 {chat_id} 失败: {result.get('error')}")
            return DeleteChatResponse(
                success=False,
                error=result.get("error", "删除失败")
            )
        
    except Exception as e:
        logger.error(f"删除会话失败: {str(e)}")
        return DeleteChatResponse(
            success=False,
            error=str(e)
        )

@router.post("/agent/chat/sessions/{chat_id}/history")
async def get_chat_history(chat_id: str, request: ChatSessionRequest):
    """
    获取会话的历史消息
    
    Args:
        chat_id: 会话ID
        request: 包含用户token的请求
    
    Returns:
        会话历史消息
    """
    try:
        # 获取认证服务和会话服务
        auth_service = get_auth_service()
        chat_session_service = get_chat_session_service()
        
        # 验证token
        try:
            rshub_token = auth_service.get_rshub_token(request.token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # 获取会话历史
        history = await chat_session_service.get_session_history(rshub_token, chat_id)
        
        logger.info(f"获取会话 {chat_id} 历史成功，共 {len(history)} 条消息")
        
        return {
            "success": True,
            "chat_id": chat_id,
            "messages": history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话历史失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }