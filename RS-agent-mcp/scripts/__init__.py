"""
脚本目录 - 包含项目设置和测试脚本
"""

from .setup import *
from .testing import *

__all__ = [
    # Setup scripts
    "reset_knowledge_base",
    "cleanup_knowledge_base", 
    "download_models",
    "fix_model_cache",
    "add_credits",
    
    # Testing scripts
    "test_rag_system",
    "test_credit_system",
    "test_chat_session_management",
    "test_fix"
]