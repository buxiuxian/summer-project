"""
RS Agent MCP 主应用启动文件
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import json
import os
import shutil
import glob
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Dict, Set
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings, get_middleware_config
from app.rag.knowledge_base import build_domain_science_db
from app.services.file_manager import cleanup_old_sessions

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# WebSocket连接管理
websocket_connections: Dict[str, Set[WebSocket]] = {}

def cleanup_temp_directory():
    """清空temp目录中的所有文件，但保留目录本身"""
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        return
    
    try:
        # 获取temp目录中的所有文件和子目录
        files_removed = 0
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    files_removed += 1
                    logger.debug(f"删除临时文件: {filename}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    files_removed += 1
                    logger.debug(f"删除临时目录: {filename}")
            except Exception as e:
                logger.warning(f"无法删除临时文件 {filename}: {e}")
        
        if files_removed > 0:
            logger.info(f"🧹 清空temp目录完成，删除了 {files_removed} 个文件/目录")
        else:
            logger.info("🧹 temp目录为空，无需清理")
            
    except Exception as e:
        logger.error(f"清理temp目录时出错: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 RS Agent MCP 正在启动...")
    
    # 启动时的初始化工作
    try:
        # 确保temp目录存在
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logger.info(f"📁 创建temp目录: {temp_dir}")
        else:
            logger.info(f"📁 temp目录已存在: {temp_dir}")
        
        # 清空temp目录（保留目录本身）
        cleanup_temp_directory()
        
        # 初始化知识库
        logger.info("📚 初始化知识库...")
        build_domain_science_db()
        
        # 清理旧的会话文件
        logger.info("🧹 清理旧的会话文件...")
        cleanup_old_sessions(settings.SESSION_CLEANUP_HOURS)
        
        logger.info("✅ 应用启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {str(e)}")
        raise
    
    yield
    
    # 关闭时的清理工作
    logger.info("🛑 RS Agent MCP 正在关闭...")
    
    # 最后一次清理会话文件
    try:
        cleanup_old_sessions(0)  # 清理所有会话文件
        logger.info("✅ 应用关闭完成！")
    except Exception as e:
        logger.error(f"❌ 应用关闭时出错: {str(e)}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

# 配置中间件
middleware_config = get_middleware_config()

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    **middleware_config["cors"]
)

# 注册API路由
app.include_router(api_router, prefix="/api/v1", tags=["api"])

# 为了兼容前端，添加/api前缀的路由
app.include_router(api_router, prefix="/api", tags=["api-compat"])

# 为了兼容前端，添加直接路由（不带/api/v1前缀）
app.include_router(api_router, tags=["direct-api"])  # 直接路由，无前缀

# WebSocket端点 - 匹配前端期望的路径
@app.websocket("/ws/progress/{session_id}")
async def websocket_progress(websocket: WebSocket, session_id: str):
    """
    WebSocket进度推送端点
    
    Args:
        websocket: WebSocket连接
        session_id: 会话ID
    """
    await websocket.accept()
    
    # 管理连接
    if session_id not in websocket_connections:
        websocket_connections[session_id] = set()
    websocket_connections[session_id].add(websocket)
    
    logger.info(f"📡 WebSocket连接建立: {session_id}")
    
    try:
        # 发送连接确认
        await websocket.send_text(json.dumps({
            "session_id": session_id,
            "message": "WebSocket连接已建立",
            "stage": "init",
            "progress": 0,
            "metadata": {}
        }))
        
        # 保持连接活跃
        while True:
            try:
                # 等待客户端消息（心跳或数据）
                data = await websocket.receive_text()
                logger.debug(f"收到WebSocket消息: {data}")
                
                # 简单的心跳响应
                await websocket.send_text(json.dumps({
                    "session_id": session_id,
                    "message": "心跳响应",
                    "stage": "heartbeat",
                    "progress": 0,
                    "metadata": {"timestamp": str(datetime.now())}
                }))
                
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info(f"📡 WebSocket连接断开: {session_id}")
    except Exception as e:
        logger.error(f"📡 WebSocket错误: {str(e)}")
    finally:
        # 清理连接
        if session_id in websocket_connections:
            websocket_connections[session_id].discard(websocket)
            if not websocket_connections[session_id]:
                del websocket_connections[session_id]

# 兼容前端的WebSocket端点 - 不带/ws前缀  
@app.websocket("/progress/{session_id}")
async def websocket_progress_compat(websocket: WebSocket, session_id: str):
    """
    WebSocket进度推送端点 - 兼容前端路径
    
    Args:
        websocket: WebSocket连接
        session_id: 会话ID
    """
    # 复用相同的逻辑
    await websocket_progress(websocket, session_id)

# 全局WebSocket进度推送函数（可被其他模块导入）
async def send_websocket_progress(session_id: str, message: str, stage: str = "processing", progress: int = 50, metadata: dict = None):
    """
    向WebSocket客户端推送进度消息
    
    Args:
        session_id: 会话ID
        message: 进度消息
        stage: 执行阶段
        progress: 进度百分比 (0-100)
        metadata: 额外元数据
    """
    if session_id in websocket_connections:
        progress_data = {
            "session_id": session_id,
            "message": message,
            "stage": stage,
            "progress": progress,
            "metadata": metadata or {}
        }
        
        # 向所有连接到该会话的WebSocket发送消息
        disconnected_connections = set()
        for websocket in websocket_connections[session_id]:
            try:
                await websocket.send_text(json.dumps(progress_data))
            except Exception as e:
                logger.warning(f"WebSocket发送失败: {e}")
                disconnected_connections.add(websocket)
        
        # 清理断开的连接
        for conn in disconnected_connections:
            websocket_connections[session_id].discard(conn)

# 根路径
@app.get("/")
async def root():
    """根路径端点"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}！",
        "version": settings.APP_VERSION,
        "description": settings.APP_DESCRIPTION,
        "docs_url": "/docs",
        "health_check": "/health",
        "api_endpoints": {
            "chat": "/agent/chat",
            "chat_upload": "/agent/chat/upload", 
            "websocket_progress": "/ws/progress/{session_id}",
            "health": "/health"
        }
    }

# 健康检查（全局）
@app.get("/health")
async def health_check():
    """全局健康检查端点"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": "development" if settings.DEBUG else "production",
        "websocket_sessions": len(websocket_connections)
    }


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {str(exc)}", exc_info=True)
    
    if settings.DEBUG:
        # 开发环境下返回详细错误信息
        return JSONResponse(
            status_code=500,
            content={
                "error": "内部服务器错误",
                "detail": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        # 生产环境下返回通用错误信息
        return JSONResponse(
            status_code=500,
            content={
                "error": "内部服务器错误",
                "detail": "服务器遇到了一个意外的情况"
            }
        )

# HTTP异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

# 开发服务器启动
if __name__ == "__main__":
    logger.info(f"🚀 在开发模式下启动 {settings.APP_NAME}")
    logger.info(f"📊 API文档: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"🔍 交互式API: http://{settings.HOST}:{settings.PORT}/redoc")
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    ) 