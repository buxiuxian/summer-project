"""
文件服务API - 处理文件下载和预览
"""

import os
from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import logging
from typing import Optional

from app.services.file_storage import file_storage_manager

logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/files", tags=["files"])

def _truncate_filename_for_display(filename: str, max_length: int = 40) -> str:
    """截断文件名用于显示，保留扩展名"""
    if len(filename) <= max_length:
        return filename
    
    # 分离文件名和扩展名
    path_obj = Path(filename)
    name = path_obj.stem
    ext = path_obj.suffix
    
    # 计算可用于文件名的长度
    available_length = max_length - len(ext)
    if available_length > 0:
        truncated_name = name[:available_length] + ext
    else:
        truncated_name = filename[:max_length]
    
    return truncated_name

@router.get("/download/{file_mapping_id}")
async def download_file(file_mapping_id: str):
    """
    下载原始文件
    
    Args:
        file_mapping_id: 文件映射ID
    
    Returns:
        文件下载响应
    """
    try:
        # 获取文件信息
        file_info = file_storage_manager.get_file_info(file_mapping_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取原始文件路径
        file_path = file_storage_manager.get_file_path(file_mapping_id, "original")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取原始文件名
        original_filename = file_info.get("original_filename", "unknown_file")
        file_extension = file_info.get("file_extension", "")
        
        # 确定媒体类型
        media_type = "application/octet-stream"
        if file_extension == ".pdf":
            media_type = "application/pdf"
        elif file_extension == ".docx":
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif file_extension == ".txt":
            media_type = "text/plain"
        elif file_extension == ".md":
            media_type = "text/markdown"
        elif file_extension == ".png":
            media_type = "image/png"
        elif file_extension == ".jpg" or file_extension == ".jpeg":
            media_type = "image/jpeg"
        elif file_extension == ".gif":
            media_type = "image/gif"
        elif file_extension == ".svg":
            media_type = "image/svg+xml"
        
        logger.info(f"下载文件: {original_filename} (ID: {file_mapping_id})")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=original_filename,
            headers={"Content-Disposition": f"attachment; filename=\"{original_filename}\""}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="下载文件失败")

@router.get("/preview/{file_mapping_id}")
async def preview_file(file_mapping_id: str):
    """
    预览文件（主要用于PDF在浏览器中打开）
    
    Args:
        file_mapping_id: 文件映射ID
    
    Returns:
        文件预览响应
    """
    try:
        # 获取文件信息
        file_info = file_storage_manager.get_file_info(file_mapping_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取原始文件路径
        file_path = file_storage_manager.get_file_path(file_mapping_id, "original")
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 获取文件扩展名
        file_extension = file_info.get("file_extension", "")
        original_filename = file_info.get("original_filename", "unknown_file")
        
        # 支持PDF和图片文件预览，其他文件直接下载
        if file_extension.lower() == ".pdf":
            logger.info(f"预览PDF文件: {original_filename} (ID: {file_mapping_id})")
            
            return FileResponse(
                path=file_path,
                media_type="application/pdf",
                filename=original_filename,
                headers={"Content-Disposition": f"inline; filename=\"{original_filename}\""}
            )
        elif file_extension.lower() in [".png", ".jpg", ".jpeg", ".gif", ".svg"]:
            logger.info(f"预览图片文件: {original_filename} (ID: {file_mapping_id})")
            
            # 确定图片媒体类型
            media_type = "application/octet-stream"
            if file_extension.lower() == ".png":
                media_type = "image/png"
            elif file_extension.lower() in [".jpg", ".jpeg"]:
                media_type = "image/jpeg"
            elif file_extension.lower() == ".gif":
                media_type = "image/gif"
            elif file_extension.lower() == ".svg":
                media_type = "image/svg+xml"
            
            return FileResponse(
                path=file_path,
                media_type=media_type,
                filename=original_filename,
                headers={"Content-Disposition": f"inline; filename=\"{original_filename}\""}
            )
        else:
            # 对于其他文件，重定向到下载接口
            logger.info(f"非预览文件，重定向到下载: {original_filename}")
            return download_file(file_mapping_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="预览文件失败")

@router.get("/info/{file_mapping_id}")
async def get_file_info(file_mapping_id: str):
    """
    获取文件信息
    
    Args:
        file_mapping_id: 文件映射ID
    
    Returns:
        文件信息
    """
    try:
        file_info = file_storage_manager.get_file_info(file_mapping_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 返回文件信息（不包含敏感路径信息）
        file_extension = file_info.get("file_extension", "").lower()
        can_preview = file_extension in [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg"]
        
        response_info = {
            "file_mapping_id": file_mapping_id,
            "original_filename": file_info.get("original_filename"),
            "display_name": file_info.get("display_name"),
            "file_extension": file_info.get("file_extension"),
            "created_time": file_info.get("created_time"),
            "can_preview": can_preview
        }
        
        return {"status": "success", "data": response_info}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件信息时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="获取文件信息失败")

@router.get("/list")
async def list_files(limit: int = Query(default=50, le=100)):
    """
    列出所有文件
    
    Args:
        limit: 返回文件数量限制
    
    Returns:
        文件列表
    """
    try:
        all_mappings = file_storage_manager.get_all_mappings()
        
        file_list = []
        for mapping_id, file_info in list(all_mappings.items())[:limit]:
            file_extension = file_info.get("file_extension", "").lower()
            can_preview = file_extension in [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".svg"]
            
            file_item = {
                "file_mapping_id": mapping_id,
                "original_filename": file_info.get("original_filename"),
                "display_name": file_info.get("display_name"),
                "file_extension": file_info.get("file_extension"),
                "created_time": file_info.get("created_time"),
                "can_preview": can_preview
            }
            file_list.append(file_item)
        
        return {
            "status": "success",
            "data": {
                "files": file_list,
                "total_count": len(all_mappings),
                "returned_count": len(file_list)
            }
        }
        
    except Exception as e:
        logger.error(f"列出文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="列出文件失败")

@router.delete("/{file_mapping_id}")
async def delete_file(file_mapping_id: str):
    """
    删除文件
    
    Args:
        file_mapping_id: 文件映射ID
    
    Returns:
        删除结果
    """
    try:
        # 获取文件信息
        file_info = file_storage_manager.get_file_info(file_mapping_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="文件不存在")
        
        original_filename = file_info.get("original_filename", "unknown_file")
        
        # 删除文件映射和相关文件
        success = file_storage_manager.delete_file_mapping(file_mapping_id)
        
        if success:
            logger.info(f"成功删除文件: {original_filename} (ID: {file_mapping_id})")
            return {"status": "success", "message": f"文件 {original_filename} 已删除"}
        else:
            raise HTTPException(status_code=500, detail="删除文件失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="删除文件失败")

@router.delete("/temp/{filename}")
async def delete_temp_image(filename: str):
    """
    删除temp目录中的图片文件（用于前端渲染完成后的清理）
    
    Args:
        filename: 图片文件名（只能是.png格式）
    
    Returns:
        删除结果
    """
    try:
        # 安全检查：只允许删除.png文件，防止路径遍历攻击
        if not filename.endswith('.png'):
            raise HTTPException(status_code=400, detail="只允许删除PNG图片文件")
        
        # 去除路径分隔符，只保留文件名
        filename = os.path.basename(filename)
        
        # 构建temp目录中的文件路径
        temp_dir = "temp"
        file_path = os.path.join(temp_dir, filename)
        
        # 确保文件路径在temp目录内（防止路径遍历）
        abs_temp_dir = os.path.abspath(temp_dir)
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(abs_temp_dir):
            raise HTTPException(status_code=400, detail="无效的文件路径")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 文件不存在也返回成功，避免重复删除的错误
            logger.info(f"temp图片文件不存在（可能已被删除）: {filename}")
            return {"status": "success", "message": f"图片文件 {filename} 不存在或已被删除"}
        
        # 删除文件
        os.remove(file_path)
        logger.info(f"成功删除temp图片文件: {filename}")
        
        return {"status": "success", "message": f"图片文件 {filename} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除temp图片文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="删除图片文件失败")

# 兼容前端老接口：/api/files/{file_id}
@router.get("/{file_id}")
async def get_file_compatible(file_id: str):
    """
    兼容前端老接口：/api/files/{file_id}
    自动判断文件类型，支持PDF/图片预览，其他类型下载
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