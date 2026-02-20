"""
文件管理服务 - 重构后的轻量级协调器
基于原始的244行代码重构为模块化架构
"""

import logging
from typing import List, Tuple, Optional
from fastapi import UploadFile

# 导入新的模块化文件服务组件
from .file.storage_service import FileStorageService
from .file.content_service import FileContentService

logger = logging.getLogger(__name__)

# 全局服务实例
storage_service = FileStorageService()
content_service = FileContentService()


async def save_uploads(files: List[UploadFile]) -> Tuple[str, List[str]]:
    """
    保存用户上传的文件到临时会话目录
    
    Args:
        files: 上传的文件列表
    
    Returns:
        Tuple[会话目录路径, 保存的文件路径列表]
    """
    try:
        # 创建会话目录
        session_path = storage_service.create_session_directory()
        
        # 准备文件数据
        files_data = []
        for file in files:
            if file.filename:
                content = await file.read()
                files_data.append((file.filename, content))
        
        # 批量保存文件
        saved_paths = storage_service.save_files_to_session(session_path, files_data)
        
        logger.info(f"成功保存 {len(saved_paths)} 个文件到会话目录: {session_path}")
        return session_path, saved_paths
        
    except Exception as e:
        logger.error(f"保存上传文件时出错: {str(e)}")
        # 如果出错，尝试清理已创建的目录
        if 'session_path' in locals():
            storage_service.cleanup_session(session_path)
        raise


def cleanup_session(session_path: str) -> bool:
    """
    清理会话目录及其所有文件
    
    Args:
        session_path: 会话目录路径
    
    Returns:
        是否成功清理
    """
    return storage_service.cleanup_session(session_path)


def create_output_file(session_path: str, filename: str, content: str) -> str:
    """
    在会话目录中创建输出文件
    
    Args:
        session_path: 会话目录路径
        filename: 文件名
        content: 文件内容
    
    Returns:
        创建的文件路径
    """
    return storage_service.create_output_file(session_path, filename, content)


def read_file_content(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件内容字符串
    """
    return content_service.read_file_content(file_path)


def get_file_info(file_paths: List[str]) -> str:
    """
    获取文件信息摘要
    
    Args:
        file_paths: 文件路径列表
    
    Returns:
        文件信息字符串
    """
    return content_service.get_files_info(file_paths)


def cleanup_old_sessions(max_age_hours: int = 24) -> int:
    """
    清理超过指定时间的旧会话目录
    
    Args:
        max_age_hours: 最大保存时间（小时）
    
    Returns:
        清理的目录数量
    """
    return storage_service.cleanup_old_sessions(max_age_hours)


# === 向后兼容的函数接口 ===
# 这些函数现在委托给相应的模块化组件

def _sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全的字符 - 委托给内容服务
    
    Args:
        filename: 原始文件名
    
    Returns:
        安全的文件名
    """
    return content_service.sanitize_filename(filename)


# === 便捷函数和高级功能 ===

def get_session_info(session_path: str) -> dict:
    """
    获取会话目录信息
    
    Args:
        session_path: 会话目录路径
    
    Returns:
        会话信息字典
    """
    return storage_service.get_session_info(session_path)


def get_storage_info() -> dict:
    """
    获取存储服务信息
    
    Returns:
        存储信息字典
    """
    return storage_service.get_storage_info()


def list_sessions() -> List[str]:
    """
    列出所有会话目录
    
    Returns:
        会话目录路径列表
    """
    return storage_service.list_sessions()


def validate_file(file_path: str, allowed_extensions: Optional[List[str]] = None) -> dict:
    """
    验证文件
    
    Args:
        file_path: 文件路径
        allowed_extensions: 允许的文件扩展名列表
    
    Returns:
        验证结果字典
    """
    return content_service.validate_file(file_path, allowed_extensions)


def get_file_preview(file_path: str, max_lines: int = 10) -> str:
    """
    获取文件预览
    
    Args:
        file_path: 文件路径
        max_lines: 最大预览行数
    
    Returns:
        文件预览字符串
    """
    return content_service.get_file_preview(file_path, max_lines)


def read_file_lines(file_path: str, max_lines: int = 1000) -> List[str]:
    """
    读取文件行
    
    Args:
        file_path: 文件路径
        max_lines: 最大读取行数
    
    Returns:
        文件行列表
    """
    return content_service.read_file_lines(file_path, max_lines)


def extract_text_from_file(file_path: str) -> str:
    """
    从文件中提取文本内容
    
    Args:
        file_path: 文件路径
    
    Returns:
        提取的文本内容
    """
    return content_service.extract_text_from_file(file_path)


def get_detailed_file_info(file_path: str) -> dict:
    """
    获取文件详细信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件详细信息字典
    """
    return content_service.get_file_info(file_path)


# === 文件管理器类 ===

class FileManager:
    """
    文件管理器类 - 提供统一的文件管理接口
    """
    
    def __init__(self):
        """初始化文件管理器"""
        self.storage_service = storage_service
        self.content_service = content_service
        logger.info("文件管理器初始化完成")
    
    async def save_uploads(self, files: List[UploadFile]) -> Tuple[str, List[str]]:
        """保存上传的文件"""
        return await save_uploads(files)
    
    def cleanup_session(self, session_path: str) -> bool:
        """清理会话目录"""
        return self.storage_service.cleanup_session(session_path)
    
    def create_output_file(self, session_path: str, filename: str, content: str) -> str:
        """创建输出文件"""
        return self.storage_service.create_output_file(session_path, filename, content)
    
    def read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        return self.content_service.read_file_content(file_path)
    
    def get_file_info(self, file_paths: List[str]) -> str:
        """获取文件信息摘要"""
        return self.content_service.get_files_info(file_paths)
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """清理旧会话目录"""
        return self.storage_service.cleanup_old_sessions(max_age_hours)
    
    def get_session_info(self, session_path: str) -> dict:
        """获取会话信息"""
        return self.storage_service.get_session_info(session_path)
    
    def get_storage_info(self) -> dict:
        """获取存储信息"""
        return self.storage_service.get_storage_info()
    
    def list_sessions(self) -> List[str]:
        """列出所有会话"""
        return self.storage_service.list_sessions()
    
    def validate_file(self, file_path: str, allowed_extensions: Optional[List[str]] = None) -> dict:
        """验证文件"""
        return self.content_service.validate_file(file_path, allowed_extensions)
    
    def get_file_preview(self, file_path: str, max_lines: int = 10) -> str:
        """获取文件预览"""
        return self.content_service.get_file_preview(file_path, max_lines)


# 创建全局文件管理器实例
file_manager = FileManager()


# 兼容性别名 - 确保现有代码不会中断
FileManagerService = FileManager
FileService = FileManager


logger.info("文件管理服务重构完成 - 从244行原始代码重构为模块化架构")
logger.info("主要改进:")
logger.info("1. 创建了FileStorageService统一管理文件存储")
logger.info("2. 分离了FileContentService处理文件内容")
logger.info("3. 重构为轻量级协调器，保持向后兼容性")
logger.info("4. 添加了会话信息、存储信息等高级功能")
logger.info("5. 支持文件验证、预览、详细分析等功能")


# 用于项目首次启动前的初始化
if __name__ == '__main__':
    print("初始化文件管理服务...")
    
    # 获取存储信息
    storage_info = get_storage_info()
    print(f"存储服务信息: {storage_info}")
    
    # 清理旧会话
    cleaned_count = cleanup_old_sessions()
    print(f"清理了 {cleaned_count} 个旧会话目录")
    
    print("文件管理服务初始化完成！")