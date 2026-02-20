"""
文件服务模块
"""

from .storage_service import FileStorageService
from .content_service import FileContentService

# 延迟导入以避免循环导入
def get_document_processor_service():
    """获取文档处理服务实例"""
    from .processor_service import document_processor_service
    return document_processor_service

def get_document_processor_class():
    """获取文档处理服务类"""
    from .processor_service import DocumentProcessorService
    return DocumentProcessorService

__all__ = [
    "FileStorageService",
    "FileContentService",
    "get_document_processor_service",
    "get_document_processor_class"
]