"""
文档处理服务
提供文件上传、转换和处理的核心功能
"""

from fastapi import HTTPException, BackgroundTasks
from typing import Optional
import logging
import tempfile
import os
from pathlib import Path

from ...agent.agent import run_analysis_agent

# 配置日志
logger = logging.getLogger(__name__)

# 支持的文件类型 (MIME类型)
SUPPORTED_FILE_TYPES = [
    "text/plain",           # .txt
    "text/markdown",        # .md
    "application/pdf",      # .pdf
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/octet-stream"  # 添加此项以支持某些浏览器将文件识别为此类型的情况
]

# 支持的文件扩展名
SUPPORTED_FILE_EXTENSIONS = ['.txt', '.md', '.pdf', '.docx']

# 直接支持的文本文件类型（无需LLM转换）
TEXT_FILE_EXTENSIONS = ['.txt', '.md']

# 需要LLM转换的文档类型
DOCUMENT_FILE_EXTENSIONS = ['.pdf', '.docx']

# 文件大小限制 (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024

class DocumentProcessorService:
    """文档处理服务类"""
    
    @staticmethod
    async def validate_and_process_file(file, background_tasks: BackgroundTasks, description: Optional[str] = None) -> dict:
        """
        验证并处理上传的文件
        
        Args:
            file: 上传的文件对象
            background_tasks: 后台任务管理器
            description: 文件描述
            
        Returns:
            处理结果字典
        """
        try:
            # 检查文件类型 - 同时检查MIME类型和文件扩展名
            file_extension = None
            if file.filename:
                file_extension = Path(file.filename).suffix.lower()
            
            # 如果是application/octet-stream，需要额外检查文件扩展名
            if file.content_type == "application/octet-stream":
                if file_extension not in SUPPORTED_FILE_EXTENSIONS:
                    raise HTTPException(
                        status_code=400,
                        detail=f"不支持的文件类型。文件扩展名: {file_extension}，支持的扩展名: {', '.join(SUPPORTED_FILE_EXTENSIONS)}"
                    )
            elif file.content_type not in SUPPORTED_FILE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(SUPPORTED_FILE_TYPES)}"
                )
            
            # 检查文件大小
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"文件太大，最大支持 {MAX_FILE_SIZE / 1024 / 1024:.1f}MB"
                )
            
            # 检查文件内容
            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="文件内容为空"
                )
            
            # 判断文件类型并选择处理方式
            if file_extension in TEXT_FILE_EXTENSIONS:
                # 直接处理文本文件(.txt, .md)
                text_content = await DocumentProcessorService._process_text_file(content, file_extension)
            elif file_extension in DOCUMENT_FILE_EXTENSIONS:
                # 使用LLM转换文档文件(.pdf, .docx)
                text_content = await DocumentProcessorService._process_document_file(content, file.filename, file_extension, background_tasks)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件扩展名: {file_extension}"
                )
            
            # 验证文本内容
            if len(text_content.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="文件内容太短，至少需要10个字符"
                )
            
            # 准备文档信息
            source_name = file.filename or "unknown_file"
            if description:
                source_name = f"{source_name} ({description})"
            
            return {
                "success": True,
                "text_content": text_content,
                "source_name": source_name,
                "original_filename": file.filename,
                "original_content": content,
                "file_size": len(content),
                "content_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"验证和处理文件时出错: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"处理文件失败: {str(e)}"
            )
    
    @staticmethod
    async def _process_text_file(content: bytes, file_extension: str) -> str:
        """处理文本文件(.txt, .md)"""
        try:
            # 尝试不同的编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'big5']:
                try:
                    text_content = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise HTTPException(
                    status_code=400,
                    detail="无法解析文件编码，请确保文件是UTF-8或GBK编码"
                )
            
            # 验证文本内容
            if len(text_content.strip()) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="文件内容太短，至少需要10个字符"
                )
            
            return text_content
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"处理文本文件时出错: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"处理文本文件失败: {str(e)}"
            )
    
    @staticmethod
    async def _process_document_file(content: bytes, filename: str, file_extension: str, background_tasks: BackgroundTasks) -> str:
        """处理文档文件(.pdf, .docx)，使用LLM转换为Markdown"""
        try:
            # 保存临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # 使用run_analysis_agent进行文档转换
                logger.info(f"开始使用LLM转换文档: {filename}")
                
                # 调用agent进行文档转换
                markdown_content = await run_analysis_agent(
                    instruction_mode=100,
                    user_prompt="",  # 对于mode 100不需要用户提示
                    file_paths=[temp_file_path],
                    output_path=None
                )
                
                # 检查转换结果
                if not markdown_content or len(markdown_content.strip()) < 100:
                    raise HTTPException(
                        status_code=400,
                        detail="LLM转换失败或生成内容过短"
                    )
                
                if markdown_content.startswith("错误："):
                    raise HTTPException(
                        status_code=400,
                        detail=f"文档转换失败: {markdown_content}"
                    )
                
                logger.info(f"成功转换文档，生成Markdown长度: {len(markdown_content)} 字符")
                return markdown_content
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"处理文档文件时出错: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"处理文档文件失败: {str(e)}"
            )
    
    @staticmethod
    def get_supported_file_types() -> dict:
        """获取支持的文件类型信息"""
        return {
            "supported_mime_types": SUPPORTED_FILE_TYPES,
            "supported_extensions": SUPPORTED_FILE_EXTENSIONS,
            "text_extensions": TEXT_FILE_EXTENSIONS,
            "document_extensions": DOCUMENT_FILE_EXTENSIONS,
            "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024
        }

# 创建服务实例
document_processor_service = DocumentProcessorService()