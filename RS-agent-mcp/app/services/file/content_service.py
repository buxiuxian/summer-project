"""
文件内容处理服务 - 处理文件读取、内容处理和信息提取
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileContentService:
    """文件内容处理服务 - 负责文件读取、内容处理和信息提取"""
    
    def __init__(self):
        """初始化文件内容处理服务"""
        self.supported_text_encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        logger.info("文件内容处理服务初始化完成")
    
    def read_file_content(self, file_path: str, encoding: Optional[str] = None) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 指定编码，如果为None则自动检测
            
        Returns:
            文件内容字符串
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                return f"错误：文件过大 ({file_size} 字节)，超过最大限制 {self.max_file_size} 字节"
            
            # 如果指定了编码，直接使用
            if encoding:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                logger.info(f"已读取文件 (指定编码 {encoding}): {file_path}")
                return content
            
            # 尝试不同的编码
            for enc in self.supported_text_encodings:
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        content = f.read()
                    logger.info(f"已读取文件 (编码 {enc}): {file_path}")
                    return content
                except UnicodeDecodeError:
                    continue
            
            # 如果都失败，返回错误信息
            logger.error(f"无法读取文件（编码问题）: {file_path}")
            return f"错误：无法读取文件 {file_path}，可能是编码问题。"
            
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            return f"错误：文件 {file_path} 不存在"
        except PermissionError:
            logger.error(f"文件权限不足: {file_path}")
            return f"错误：没有权限读取文件 {file_path}"
        except Exception as e:
            logger.error(f"读取文件时出错: {str(e)}")
            return f"错误：读取文件 {file_path} 时出现问题：{str(e)}"
    
    def read_file_lines(self, file_path: str, max_lines: int = 1000) -> List[str]:
        """
        读取文件行
        
        Args:
            file_path: 文件路径
            max_lines: 最大读取行数
            
        Returns:
            文件行列表
        """
        try:
            lines = []
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip('\n'))
            
            logger.info(f"已读取文件 {len(lines)} 行: {file_path}")
            return lines
            
        except UnicodeDecodeError:
            # 尝试其他编码
            for enc in ['gbk', 'gb2312', 'latin1']:
                try:
                    lines = []
                    with open(file_path, "r", encoding=enc) as f:
                        for i, line in enumerate(f):
                            if i >= max_lines:
                                break
                            lines.append(line.rstrip('\n'))
                    
                    logger.info(f"已读取文件 {len(lines)} 行 (编码 {enc}): {file_path}")
                    return lines
                except UnicodeDecodeError:
                    continue
            
            logger.error(f"无法读取文件行（编码问题）: {file_path}")
            return []
            
        except Exception as e:
            logger.error(f"读取文件行时出错: {str(e)}")
            return []
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件详细信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            path_obj = Path(file_path)
            
            if not path_obj.exists():
                return {'exists': False, 'path': file_path}
            
            stat = path_obj.stat()
            
            info = {
                'exists': True,
                'path': file_path,
                'name': path_obj.name,
                'stem': path_obj.stem,
                'suffix': path_obj.suffix,
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'is_file': path_obj.is_file(),
                'is_dir': path_obj.is_dir()
            }
            
            # 如果是文件，添加额外信息
            if path_obj.is_file():
                # 尝试检测文件类型
                info['file_type'] = self._detect_file_type(path_obj.suffix)
                
                # 尝试读取前几行
                try:
                    sample_lines = self.read_file_lines(file_path, 5)
                    info['sample_lines'] = sample_lines
                    info['line_count'] = len(sample_lines)
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"获取文件信息时出错: {str(e)}")
            return {'exists': False, 'path': file_path, 'error': str(e)}
    
    def get_files_info(self, file_paths: List[str]) -> str:
        """
        获取多个文件的信息摘要
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            文件信息字符串
        """
        if not file_paths:
            return "没有上传文件"
        
        file_info = []
        total_size = 0
        
        for file_path in file_paths:
            info = self.get_file_info(file_path)
            if info['exists']:
                size = info['size']
                total_size += size
                file_info.append(f"- {info['name']} ({size} 字节)")
            else:
                file_info.append(f"- {info.get('name', os.path.basename(file_path))} (文件不存在)")
        
        summary = f"上传文件 ({len(file_paths)} 个，总大小 {total_size} 字节):\n"
        return summary + "\n".join(file_info)
    
    def _detect_file_type(self, suffix: str) -> str:
        """
        根据文件扩展名检测文件类型
        
        Args:
            suffix: 文件扩展名
            
        Returns:
            文件类型描述
        """
        suffix = suffix.lower()
        
        type_mapping = {
            '.txt': '文本文件',
            '.md': 'Markdown文件',
            '.py': 'Python源代码',
            '.js': 'JavaScript源代码',
            '.html': 'HTML文件',
            '.css': 'CSS样式表',
            '.json': 'JSON数据',
            '.xml': 'XML文件',
            '.csv': 'CSV数据',
            '.pdf': 'PDF文档',
            '.doc': 'Word文档',
            '.docx': 'Word文档',
            '.xls': 'Excel表格',
            '.xlsx': 'Excel表格',
            '.jpg': 'JPEG图片',
            '.jpeg': 'JPEG图片',
            '.png': 'PNG图片',
            '.bmp': 'BMP图片',
            '.tiff': 'TIFF图片'
        }
        
        return type_mapping.get(suffix, '未知类型')
    
    def validate_file(self, file_path: str, allowed_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        验证文件
        
        Args:
            file_path: 文件路径
            allowed_extensions: 允许的文件扩展名列表
            
        Returns:
            验证结果字典
        """
        try:
            info = self.get_file_info(file_path)
            
            if not info['exists']:
                return {'valid': False, 'reason': '文件不存在'}
            
            # 检查文件大小
            if info['size'] > self.max_file_size:
                return {
                    'valid': False, 
                    'reason': f'文件过大 ({info["size_mb"]} MB)，超过最大限制 {self.max_file_size / (1024*1024):.1f} MB'
                }
            
            # 检查文件扩展名
            if allowed_extensions:
                if info['suffix'].lower() not in allowed_extensions:
                    return {
                        'valid': False,
                        'reason': f'文件类型 {info["suffix"]} 不在允许的列表中'
                    }
            
            return {'valid': True, 'info': info}
            
        except Exception as e:
            logger.error(f"验证文件时出错: {str(e)}")
            return {'valid': False, 'reason': f'验证时出错: {str(e)}'}
    
    def get_file_preview(self, file_path: str, max_lines: int = 10) -> str:
        """
        获取文件预览
        
        Args:
            file_path: 文件路径
            max_lines: 最大预览行数
            
        Returns:
            文件预览字符串
        """
        try:
            lines = self.read_file_lines(file_path, max_lines)
            if not lines:
                return "文件为空或无法读取"
            
            preview = f"文件预览 ({len(lines)} 行):\n"
            preview += "---\n"
            preview += '\n'.join(lines)
            preview += "\n---"
            
            if len(lines) == max_lines:
                preview += f"\n... (显示前 {max_lines} 行)"
            
            return preview
            
        except Exception as e:
            logger.error(f"获取文件预览时出错: {str(e)}")
            return f"获取文件预览时出错: {str(e)}"
    
    def extract_text_from_file(self, file_path: str) -> str:
        """
        从文件中提取文本内容
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        return self.read_file_content(file_path)
    
    def sanitize_filename(self, filename: str) -> str:
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