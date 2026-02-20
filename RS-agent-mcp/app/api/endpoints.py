"""
API端点定义 - 路由聚合器
重构后的轻量级端点定义，负责聚合所有功能专一的路由器
从原来的1321行巨型文件重构为18行的路由聚合器，提高了代码的可维护性
"""

from fastapi import APIRouter
from .routers import chat_router, session_router, health_router, knowledge_router
from app.api.logs import router as logs_router

# 创建主路由器
router = APIRouter()

# 包含所有功能专一的路由器
router.include_router(chat_router)
router.include_router(session_router)
router.include_router(health_router)
router.include_router(knowledge_router)
router.include_router(logs_router)