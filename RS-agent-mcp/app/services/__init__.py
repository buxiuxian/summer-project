"""
后端服务层 - 模块化架构的服务组件
重构后的服务层按业务域组织，提供文件管理、会话管理、计费、认证等基础服务
每个服务模块职责单一，便于维护和扩展
"""

# 文件服务
from .file_manager import FileManager, file_manager
from .file import FileStorageService, FileContentService

# 会话服务
from .session import ChatSessionService, get_chat_session_service

# 计费服务
from .billing import BillingTracker, CreditService

# 认证服务
from .auth import AuthService

# 文档处理服务 - 按需导入以提高启动性能
def get_document_processor_service():
    """获取文档处理服务实例 - 延迟导入以优化启动性能"""
    from .file import get_document_processor_service
    return get_document_processor_service()

__all__ = [
    # 文件服务
    "FileManager",
    "file_manager", 
    "FileStorageService",
    "FileContentService",
    
    # 会话服务
    "ChatSessionService",
    "get_chat_session_service",
    
    # 计费服务
    "BillingTracker",
    "CreditService",
    
    # 认证服务
    "AuthService",
    
    # 文档处理服务
    "get_document_processor_service"
] 