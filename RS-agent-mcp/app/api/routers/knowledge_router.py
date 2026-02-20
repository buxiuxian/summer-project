"""
知识库管理API - 处理文档上传和知识库管理
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List
import logging
import io
import os
from pathlib import Path

from ...rag.knowledge_base import knowledge_manager, add_document_to_knowledge_base
from ...services.file_storage import file_storage_manager
from ...services.file.processor_service import document_processor_service

# 配置日志
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    description: Optional[str] = None
):
    """
    上传文档到知识库
    
    Args:
        file: 上传的文件
        description: 文件描述
    
    Returns:
        上传结果
    """
    try:
        # 使用文档处理服务验证和处理文件
        process_result = await document_processor_service.validate_and_process_file(file, background_tasks, description)
        
        # 在后台添加文档到知识库，并保存原始文件
        background_tasks.add_task(
            _add_document_background,
            process_result["text_content"],
            process_result["source_name"],
            process_result["original_filename"],
            process_result["original_content"]
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "文档上传成功，正在后台处理并添加到知识库",
                "filename": process_result["original_filename"],
                "size": process_result["file_size"],
                "content_preview": process_result["content_preview"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传文档时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"上传文档失败: {str(e)}"
        )


async def _add_document_background(content: str, source_name: str, filename: str, original_content: bytes):
    """后台任务：添加文档到知识库并保存原始文件"""
    try:
        logger.info(f"开始处理上传的文档: {filename}")
        
        # 创建文件映射关系
        file_mapping_id = None
        try:
            # 对于所有文档类型，都保存转换后的内容到converted目录
            # 这样重启时知识库重建可以从converted目录找到所有文件
            file_extension = Path(filename).suffix.lower() if filename else ""
            
            # 对于所有支持的文件类型，都保存转换内容
            if file_extension in ['.txt', '.md', '.pdf', '.docx']:
                converted_content = content
            else:
                converted_content = None
            
            file_mapping_id = file_storage_manager.create_file_mapping(
                original_filename=filename,
                original_content=original_content,
                converted_content=converted_content
            )
            logger.info(f"文件映射关系已创建: {file_mapping_id}")
        except Exception as e:
            logger.error(f"创建文件映射关系失败: {str(e)}")
        
        # 直接添加到知识库（文件已通过file_storage_manager保存）
        success = knowledge_manager.add_document(content, filename, file_mapping_id)
        
        if success:
            logger.info(f"成功添加文档到知识库: {filename}")
        else:
            logger.error(f"添加文档到知识库失败: {filename}")
            # 如果添加失败，清理文件映射
            if file_mapping_id:
                file_storage_manager.delete_file_mapping(file_mapping_id)
            
    except Exception as e:
        logger.error(f"后台处理文档时出错: {str(e)}")

@router.post("/rebuild")
async def rebuild_knowledge_base(background_tasks: BackgroundTasks):
    """
    重新构建知识库
    
    Returns:
        重建结果
    """
    try:
        # 在后台重建知识库
        background_tasks.add_task(_rebuild_knowledge_base_background)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "知识库重建任务已启动，正在后台处理"
            }
        )
        
    except Exception as e:
        logger.error(f"启动知识库重建时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"启动知识库重建失败: {str(e)}"
        )

async def _rebuild_knowledge_base_background():
    """后台任务：重建知识库"""
    try:
        logger.info("开始重建知识库...")
        
        # 重新构建索引
        knowledge_manager.build_index_from_sources()
        
        logger.info("知识库重建完成")
        
    except Exception as e:
        logger.error(f"重建知识库时出错: {str(e)}")

@router.get("/status")
async def get_knowledge_base_status():
    """
    获取知识库状态
    
    Returns:
        知识库状态信息
    """
    try:
        # 获取索引状态
        total_docs = 0
        index_exists = False
        
        index_info = knowledge_manager.get_index_info()
        total_docs = index_info.get('total_documents', 0)
        index_exists = index_info.get('status', '') == 'available'
        
        # 获取源文档数量
        source_files = []
        all_mappings = file_storage_manager.get_all_mappings()
        
        for mapping_id, file_info in all_mappings.items():
            try:
                original_path = file_info.get("original_path")
                if original_path and os.path.exists(original_path):
                    file_stat = Path(original_path).stat()
                    source_files.append({
                        "name": file_info.get("display_name", file_info.get("original_filename", "unknown")),
                        "size": file_stat.st_size,
                        "modified": file_stat.st_mtime
                    })
            except Exception as e:
                logger.warning(f"获取文件状态失败 {mapping_id}: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "index_exists": index_exists,
                    "total_document_chunks": total_docs,
                    "source_files_count": len(source_files),
                    "source_files": source_files,  # 返回所有文件
                    "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取知识库状态时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取知识库状态失败: {str(e)}"
        )

@router.delete("/document/{filename}")
async def delete_document(filename: str, background_tasks: BackgroundTasks):
    """
    删除指定文档
    
    Args:
        filename: 文件名
    
    Returns:
        删除结果
    """
    try:
        logger.info(f"开始删除文档: {filename}")
        
        # 查找文件映射ID
        file_mapping_id = None
        all_mappings = file_storage_manager.get_all_mappings()
        
        for mapping_id, file_info in all_mappings.items():
            if (file_info.get('original_filename') == filename or 
                file_info.get('display_name') == filename):
                file_mapping_id = mapping_id
                break
        
        # 尝试从知识库中删除文档（按source删除）
        delete_success = knowledge_manager.delete_document_by_source(filename)
        
        if not delete_success:
            # 如果按原始文件名删除失败，可能需要尝试其他可能的source名称
            logger.info(f"按文件名 {filename} 删除失败，尝试查找相关的source...")
            
            # 获取所有文档映射，寻找可能相关的source
            if hasattr(knowledge_manager, 'doc_mapping') and knowledge_manager.doc_mapping:
                potential_sources = []
                for doc_info in knowledge_manager.doc_mapping.values():
                    source = doc_info.get('source', '')
                    # 检查source是否包含文件名的主要部分
                    filename_base = Path(filename).stem
                    if filename_base in source or source in filename:
                        potential_sources.append(source)
                
                # 去重
                potential_sources = list(set(potential_sources))
                
                # 尝试删除找到的相关source
                for source in potential_sources:
                    logger.info(f"尝试删除source: {source}")
                    if knowledge_manager.delete_document_by_source(source):
                        delete_success = True
                        logger.info(f"成功删除source: {source}")
                        break
        
        # 删除文件存储中的文件
        file_deleted = False
        if file_mapping_id:
            file_deleted = file_storage_manager.delete_file_mapping(file_mapping_id)
            logger.info(f"删除文件存储映射: {file_mapping_id}, 结果: {file_deleted}")
        
        if delete_success:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": f"文件 {filename} 已成功删除",
                    "file_deleted": file_deleted,
                    "index_updated": True
                }
            )
        else:
            # 如果精确删除失败，提供重建选项
            logger.warning(f"精确删除失败，可能需要重建知识库")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "partial_success",
                    "message": f"物理文件已删除，但知识库索引可能需要重建",
                    "file_deleted": file_deleted,
                    "index_updated": False,
                    "suggestion": "如果问题持续存在，请尝试重建知识库"
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文档时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除文档失败: {str(e)}"
        )

@router.get("/search")
async def search_knowledge(query: str, limit: int = 5):
    """
    搜索知识库
    
    Args:
        query: 搜索查询
        limit: 返回结果数量限制
    
    Returns:
        搜索结果
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=400,
                detail="搜索查询不能为空"
            )
        
        # 构建关键词列表
        keywords = [{"keyword": query, "weight": 1.0}]
        
        # 搜索知识库，获取结构化结果
        results = knowledge_manager.query_knowledge_structured(keywords, top_k=limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "query": query,
                    "results": results,
                    "total_results": len(results)
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索知识库时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索知识库失败: {str(e)}"
        )

@router.get("/debug")
async def get_knowledge_debug_info():
    """
    获取知识库调试信息
    
    Returns:
        知识库的详细调试信息
    """
    try:
        debug_info = {
            "index_type": "FAISS" if knowledge_manager.use_sentence_transformers else "TF-IDF",
            "total_chunks": 0,
            "documents": [],
            "physical_files": [],
            "mapping_info": {}
        }
        
        # 获取索引信息
        index_info = knowledge_manager.get_index_info()
        debug_info["total_chunks"] = index_info.get('total_documents', 0)
        
        # 获取文档映射信息
        if hasattr(knowledge_manager, 'doc_mapping') and knowledge_manager.doc_mapping:
            sources_count = {}
            for idx, doc_info in knowledge_manager.doc_mapping.items():
                source = doc_info.get('source', 'unknown')
                if source not in sources_count:
                    sources_count[source] = 0
                sources_count[source] += 1
                
                # 收集详细的文档信息
                debug_info["documents"].append({
                    "index": idx,
                    "source": source,
                    "physical_file": doc_info.get('physical_file', ''),
                    "original_filename": doc_info.get('original_filename', ''),
                    "chunk_id": doc_info.get('chunk_id', ''),
                    "text_preview": doc_info.get('text', '')[:100] + "..." if len(doc_info.get('text', '')) > 100 else doc_info.get('text', '')
                })
            
            debug_info["mapping_info"] = sources_count
        
        # 获取物理文件列表
        all_mappings = file_storage_manager.get_all_mappings()
        for mapping_id, file_info in all_mappings.items():
            try:
                original_path = file_info.get("original_path")
                if original_path and os.path.exists(original_path):
                    file_stat = Path(original_path).stat()
                    debug_info["physical_files"].append({
                        "name": file_info.get("display_name", file_info.get("original_filename", "unknown")),
                        "size": file_stat.st_size,
                        "extension": file_info.get("file_extension", ""),
                        "mapping_id": mapping_id
                    })
            except Exception as e:
                logger.warning(f"获取文件信息失败 {mapping_id}: {str(e)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": debug_info
            }
        )
        
    except Exception as e:
        logger.error(f"获取调试信息时出错: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取调试信息失败: {str(e)}"
        )

@router.get("/download/{file_id}")
async def download_knowledge_file(file_id: str):
    """
    通过文件哈希ID下载知识库中的原始文件，Content-Disposition使用原始文件名
    """
    file_info = file_storage_manager.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    file_path = file_storage_manager.get_file_path(file_id, "original")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    original_filename = file_info.get("original_filename", "unknown_file")
    return FileResponse(
        path=file_path,
        filename=original_filename,
        headers={"Content-Disposition": f"attachment; filename=\"{original_filename}\""}
    )

@router.get("/preview/{file_id}")
async def preview_knowledge_file(file_id: str):
    """
    通过文件哈希ID预览知识库中的文件，支持pdf和图片inline预览，其他类型自动下载
    """
    file_info = file_storage_manager.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")
    file_path = file_storage_manager.get_file_path(file_id, "original")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    file_extension = file_info.get("file_extension", "").lower()
    original_filename = file_info.get("original_filename", "unknown_file")
    # PDF/图片直接预览，其他类型下载
    if file_extension in [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg"]:
        media_type = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".svg": "image/svg+xml"
        }.get(file_extension, "application/octet-stream")
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=original_filename,
            headers={"Content-Disposition": f"inline; filename=\"{original_filename}\""}
        )
    else:
        return FileResponse(
            path=file_path,
            media_type="application/octet-stream",
            filename=original_filename,
            headers={"Content-Disposition": f"attachment; filename=\"{original_filename}\""}
        ) 