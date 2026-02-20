"""
API路由器模块
"""

from .chat_router import router as chat_router
from .session_router import router as session_router
from .health_router import router as health_router
from .knowledge_router import router as knowledge_router

__all__ = [
    "chat_router",
    "session_router",
    "health_router",
    "knowledge_router"
]