"""
API接口层 - 提供HTTP端点服务
"""

from fastapi import APIRouter
from .endpoints import router as endpoints_router
from .logs import router as logs_router
from .progress import router as progress_router
from .files import router as files_router

# 创建主API路由器
api_router = APIRouter()

# 包含各个子路由
api_router.include_router(endpoints_router)
api_router.include_router(logs_router)
api_router.include_router(progress_router)
api_router.include_router(files_router)

__all__ = ["api_router"] 