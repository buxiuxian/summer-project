"""
文件存储服务 - 处理文件存储、目录管理和清理
"""

import os
import uuid
import shutil
import tempfile
from typing import List, Tuple, Optional
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)


class FileStorageService:
    """文件存储服务 - 负责文件存储、目录管理和清理"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        初始化文件存储服务
        
        Args:
            temp_dir: 临时目录路径，默认为系统临时目录下的rs_agent_sessions
        """
        self.temp_dir = temp_dir or os.path.join(tempfile.gettempdir(), "rs_agent_sessions")
        self._ensure_temp_dir()
    
    def _ensure_temp_dir(self):
        """确保临时目录存在"""
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"文件存储服务初始化，临时目录: {self.temp_dir}")
    
    def create_session_directory(self) -> str:
        """
        创建唯一的会话目录
        
        Returns:
            会话目录路径
        """
        session_id = str(uuid.uuid4())
        session_path = os.path.join(self.temp_dir, session_id)
        os.makedirs(session_path, exist_ok=True)
        logger.info(f"创建会话目录: {session_path}")
        return session_path
    
    def save_file_to_session(self, session_path: str, filename: str, content: bytes) -> str:
        """
        保存文件到会话目录
        
        Args:
            session_path: 会话目录路径
            filename: 文件名
            content: 文件内容
            
        Returns:
            保存的文件路径
        """
        try:
            # 确保会话目录存在
            os.makedirs(session_path, exist_ok=True)
            
            # 构建安全的文件路径
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(session_path, safe_filename)
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            logger.info(f"文件已保存: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"保存文件时出错: {str(e)}")
            raise
    
    def save_files_to_session(self, session_path: str, files_data: List[Tuple[str, bytes]]) -> List[str]:
        """
        批量保存文件到会话目录
        
        Args:
            session_path: 会话目录路径
            files_data: 文件数据列表，每个元素为(filename, content)元组
            
        Returns:
            保存的文件路径列表
        """
        saved_paths = []
        
        for filename, content in files_data:
            try:
                file_path = self.save_file_to_session(session_path, filename, content)
                saved_paths.append(file_path)
            except Exception as e:
                logger.error(f"保存文件 {filename} 失败: {str(e)}")
                continue
        
        return saved_paths
    
    def create_output_file(self, session_path: str, filename: str, content: str) -> str:
        """
        在会话目录中创建输出文件
        
        Args:
            session_path: 会话目录路径
            filename: 文件名
            content: 文件内容
            
        Returns:
            创建的文件路径
        """
        try:
            # 确保会话目录存在
            os.makedirs(session_path, exist_ok=True)
            
            safe_filename = self._sanitize_filename(filename)
            file_path = os.path.join(session_path, safe_filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"输出文件已创建: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"创建输出文件时出错: {str(e)}")
            raise
    
    def cleanup_session(self, session_path: str) -> bool:
        """
        清理会话目录及其所有文件
        
        Args:
            session_path: 会话目录路径
            
        Returns:
            是否成功清理
        """
        try:
            if os.path.exists(session_path):
                shutil.rmtree(session_path)
                logger.info(f"会话目录已清理: {session_path}")
                return True
            else:
                logger.warning(f"会话目录不存在: {session_path}")
                return True
                
        except Exception as e:
            logger.error(f"清理会话目录时出错: {str(e)}")
            return False
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        清理超过指定时间的旧会话目录
        
        Args:
            max_age_hours: 最大保存时间（小时）
            
        Returns:
            清理的目录数量
        """
        try:
            if not os.path.exists(self.temp_dir):
                return 0
            
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for session_dir in os.listdir(self.temp_dir):
                session_path = os.path.join(self.temp_dir, session_dir)
                
                if os.path.isdir(session_path):
                    # 获取目录创建时间
                    dir_time = os.path.getctime(session_path)
                    
                    if current_time - dir_time > max_age_seconds:
                        if self.cleanup_session(session_path):
                            cleaned_count += 1
            
            logger.info(f"清理了 {cleaned_count} 个旧会话目录")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理旧会话时出错: {str(e)}")
            return 0
    
    def get_session_info(self, session_path: str) -> dict:
        """
        获取会话目录信息
        
        Args:
            session_path: 会话目录路径
            
        Returns:
            会话信息字典
        """
        try:
            if not os.path.exists(session_path):
                return {'exists': False}
            
            path_obj = Path(session_path)
            files = list(path_obj.glob('*'))
            
            info = {
                'exists': True,
                'path': session_path,
                'file_count': len(files),
                'total_size': sum(f.stat().st_size for f in files if f.is_file()),
                'files': [f.name for f in files if f.is_file()],
                'directories': [d.name for d in files if d.is_dir()]
            }
            
            # 获取创建时间
            stat = path_obj.stat()
            info['created_time'] = stat.st_ctime
            info['modified_time'] = stat.st_mtime
            
            return info
            
        except Exception as e:
            logger.error(f"获取会话信息时出错: {str(e)}")
            return {'exists': False, 'error': str(e)}
    
    def get_storage_info(self) -> dict:
        """
        获取存储服务信息
        
        Returns:
            存储信息字典
        """
        try:
            total_size = 0
            session_count = 0
            file_count = 0
            
            if os.path.exists(self.temp_dir):
                for session_dir in os.listdir(self.temp_dir):
                    session_path = os.path.join(self.temp_dir, session_dir)
                    if os.path.isdir(session_path):
                        session_count += 1
                        session_info = self.get_session_info(session_path)
                        total_size += session_info.get('total_size', 0)
                        file_count += session_info.get('file_count', 0)
            
            return {
                'temp_dir': self.temp_dir,
                'session_count': session_count,
                'total_files': file_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"获取存储信息时出错: {str(e)}")
            return {'error': str(e)}
    
    def list_sessions(self) -> List[str]:
        """
        列出所有会话目录
        
        Returns:
            会话目录路径列表
        """
        try:
            sessions = []
            if os.path.exists(self.temp_dir):
                for session_dir in os.listdir(self.temp_dir):
                    session_path = os.path.join(self.temp_dir, session_dir)
                    if os.path.isdir(session_path):
                        sessions.append(session_path)
            
            return sorted(sessions, key=lambda x: os.path.getctime(x), reverse=True)
            
        except Exception as e:
            logger.error(f"列出会话时出错: {str(e)}")
            return []
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        清理文件名，移除不安全的字符
        
        Args:
            filename: 原始文件名
            
        Returns:
            安全的文件名
        """
        # 移除路径分隔符和其他危险字符
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        safe_name = filename
        
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        
        # 限制文件名长度
        if len(safe_name) > 255:
            name_part = safe_name[:200]
            ext_part = safe_name[-50:] if '.' in safe_name[-50:] else ''
            safe_name = name_part + '_truncated_' + ext_part
        
        return safe_name
    
    def file_exists(self, file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        return os.path.exists(file_path)
    
    def get_file_size(self, file_path: str) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        try:
            return os.path.getsize(file_path)
        except Exception:
            return 0
    
    def is_temp_file(self, file_path: str) -> bool:
        """
        检查文件是否是临时文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否是临时文件
        """
        return file_path.startswith(self.temp_dir)