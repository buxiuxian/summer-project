"""
文件存储服务 - 管理上传的原始文件及其映射关系
"""

import os
import json
import shutil
import hashlib
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 文件存储配置
STORAGE_ROOT = "file_storage"
STORAGE_ORIGINALS = os.path.join(STORAGE_ROOT, "originals")
STORAGE_CONVERTED = os.path.join(STORAGE_ROOT, "converted")
MAPPING_FILE = os.path.join(STORAGE_ROOT, "file_mapping.json")

class FileStorageManager:
    """文件存储管理器"""
    
    def __init__(self):
        self.storage_root = STORAGE_ROOT
        self.originals_dir = STORAGE_ORIGINALS
        self.converted_dir = STORAGE_CONVERTED
        self.mapping_file = MAPPING_FILE
        self.file_mapping = {}
        
        # 初始化存储目录
        self._init_storage_dirs()
        self._load_mapping()
    
    def _init_storage_dirs(self):
        """初始化存储目录"""
        for dir_path in [self.storage_root, self.originals_dir, self.converted_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def _load_mapping(self):
        """加载文件映射关系"""
        try:
            if os.path.exists(self.mapping_file):
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.file_mapping = json.load(f)
                logger.info(f"已加载文件映射关系: {len(self.file_mapping)} 个条目")
            else:
                self.file_mapping = {}
        except Exception as e:
            logger.error(f"加载文件映射关系失败: {str(e)}")
            self.file_mapping = {}
    
    def _save_mapping(self):
        """保存文件映射关系"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_mapping, f, ensure_ascii=False, indent=2)
            logger.info("文件映射关系已保存")
        except Exception as e:
            logger.error(f"保存文件映射关系失败: {str(e)}")
    
    def _generate_file_id(self, filename: str, content: bytes) -> str:
        """生成文件唯一ID"""
        # 使用文件名和内容的哈希值生成唯一ID
        hasher = hashlib.md5()
        hasher.update(filename.encode('utf-8'))
        hasher.update(content)
        return hasher.hexdigest()
    
    def _truncate_filename_for_display(self, filename: str, max_length: int = 40) -> str:
        """截断文件名用于显示，保留扩展名"""
        if len(filename) <= max_length:
            return filename
        
        # 分离文件名和扩展名
        path_obj = Path(filename)
        name = path_obj.stem
        ext = path_obj.suffix
        
        # 计算可用于文件名的长度（减去"..."的3个字符）
        available_length = max_length - len(ext) - 3
        if available_length > 0:
            truncated_name = name[:available_length] + "..." + ext
        else:
            # 如果扩展名太长，直接截断整个文件名
            truncated_name = filename[:max_length-3] + "..."
        
        return truncated_name
    
    def store_file(self, filename: str, content: bytes, file_type: str = "original") -> Tuple[str, str]:
        """
        存储文件
        
        Args:
            filename: 原始文件名
            content: 文件内容
            file_type: 文件类型 ("original" 或 "converted")
        
        Returns:
            Tuple[文件ID, 存储路径]
        """
        try:
            # 生成文件ID
            file_id = self._generate_file_id(filename, content)
            
            # 确定存储目录
            storage_dir = self.originals_dir if file_type == "original" else self.converted_dir
            
            # 创建存储路径
            file_extension = Path(filename).suffix
            stored_filename = f"{file_id}{file_extension}"
            storage_path = os.path.join(storage_dir, stored_filename)
            
            # 如果文件已存在，直接返回
            if os.path.exists(storage_path):
                logger.info(f"文件已存在: {storage_path}")
                return file_id, storage_path
            
            # 保存文件
            with open(storage_path, 'wb') as f:
                f.write(content)
            
            logger.info(f"文件已存储: {storage_path}")
            return file_id, storage_path
            
        except Exception as e:
            logger.error(f"存储文件失败: {str(e)}")
            raise
    
    def create_file_mapping(self, original_filename: str, original_content: bytes, 
                          converted_content: Optional[str] = None) -> str:
        """
        创建文件映射关系
        
        Args:
            original_filename: 原始文件名
            original_content: 原始文件内容
            converted_content: 转换后的文本内容
        
        Returns:
            文件映射ID
        """
        try:
            # 存储原始文件
            original_file_id, original_path = self.store_file(original_filename, original_content, "original")
            
            # 准备映射信息
            mapping_info = {
                "original_filename": original_filename,
                "original_file_id": original_file_id,
                "original_path": original_path,
                "file_extension": Path(original_filename).suffix.lower(),
                "display_name": self._truncate_filename_for_display(original_filename),
                "created_time": str(Path(original_path).stat().st_mtime) if os.path.exists(original_path) else None
            }
            
            # 如果有转换内容，也保存转换后的文件
            if converted_content:
                converted_filename = f"{Path(original_filename).stem}_converted.txt"
                converted_content_bytes = converted_content.encode('utf-8')
                converted_file_id, converted_path = self.store_file(converted_filename, converted_content_bytes, "converted")
                
                mapping_info.update({
                    "converted_file_id": converted_file_id,
                    "converted_path": converted_path,
                    "converted_filename": converted_filename
                })
            
            # 保存映射关系
            mapping_id = original_file_id  # 使用原始文件ID作为映射ID
            self.file_mapping[mapping_id] = mapping_info
            self._save_mapping()
            
            logger.info(f"文件映射关系已创建: {mapping_id}")
            return mapping_id
            
        except Exception as e:
            logger.error(f"创建文件映射关系失败: {str(e)}")
            raise
    
    def get_file_info(self, mapping_id: str) -> Optional[Dict]:
        """获取文件信息"""
        return self.file_mapping.get(mapping_id)
    
    def get_file_path(self, mapping_id: str, file_type: str = "original") -> Optional[str]:
        """
        获取文件路径
        
        Args:
            mapping_id: 映射ID
            file_type: 文件类型 ("original" 或 "converted")
        
        Returns:
            文件路径
        """
        mapping_info = self.file_mapping.get(mapping_id)
        if not mapping_info:
            return None
        
        if file_type == "original":
            return mapping_info.get("original_path")
        elif file_type == "converted":
            return mapping_info.get("converted_path")
        
        return None
    
    def get_all_mappings(self) -> Dict[str, Dict]:
        """获取所有文件映射关系"""
        return self.file_mapping.copy()
    
    def delete_file_mapping(self, mapping_id: str) -> bool:
        """
        删除文件映射关系及相关文件
        
        Args:
            mapping_id: 映射ID
        
        Returns:
            是否成功删除
        """
        try:
            mapping_info = self.file_mapping.get(mapping_id)
            if not mapping_info:
                logger.warning(f"映射ID不存在: {mapping_id}")
                return False
            
            # 删除原始文件
            original_path = mapping_info.get("original_path")
            if original_path and os.path.exists(original_path):
                os.remove(original_path)
                logger.info(f"已删除原始文件: {original_path}")
            
            # 删除转换文件
            converted_path = mapping_info.get("converted_path")
            if converted_path and os.path.exists(converted_path):
                os.remove(converted_path)
                logger.info(f"已删除转换文件: {converted_path}")
            
            # 删除映射关系
            del self.file_mapping[mapping_id]
            self._save_mapping()
            
            logger.info(f"文件映射关系已删除: {mapping_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件映射关系失败: {str(e)}")
            return False
    
    def create_converted_file(self, mapping_id: str, converted_content: str) -> bool:
        """
        为已存在的文件映射创建转换文件
        
        Args:
            mapping_id: 文件映射ID
            converted_content: 转换后的文本内容
        
        Returns:
            是否成功创建
        """
        try:
            mapping_info = self.file_mapping.get(mapping_id)
            if not mapping_info:
                logger.error(f"映射ID不存在: {mapping_id}")
                return False
            
            # 如果已经有转换文件，跳过
            if mapping_info.get("converted_path"):
                logger.info(f"映射 {mapping_id} 已有转换文件，跳过")
                return True
            
            # 创建转换文件
            original_filename = mapping_info.get("original_filename", "unknown")
            converted_filename = f"{Path(original_filename).stem}_converted.txt"
            converted_content_bytes = converted_content.encode('utf-8')
            converted_file_id, converted_path = self.store_file(converted_filename, converted_content_bytes, "converted")
            
            # 更新映射信息
            mapping_info.update({
                "converted_file_id": converted_file_id,
                "converted_path": converted_path,
                "converted_filename": converted_filename
            })
            
            # 保存映射关系
            self._save_mapping()
            
            logger.info(f"为映射 {mapping_id} 创建了转换文件: {converted_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建转换文件失败: {str(e)}")
            return False
    
    def search_by_source_name(self, source_name: str) -> List[str]:
        """
        根据源文件名搜索映射ID
        
        Args:
            source_name: 源文件名（可能包含描述信息）
        
        Returns:
            匹配的映射ID列表
        """
        matching_ids = []
        for mapping_id, mapping_info in self.file_mapping.items():
            original_filename = mapping_info.get("original_filename", "")
            
            # 检查是否匹配原始文件名或包含在source_name中
            if original_filename == source_name or original_filename in source_name:
                matching_ids.append(mapping_id)
        
        return matching_ids
    
    def cleanup_orphaned_files(self) -> int:
        """清理孤立的文件（没有映射关系的文件）"""
        try:
            cleaned_count = 0
            
            # 获取所有映射中的文件路径
            mapped_files = set()
            for mapping_info in self.file_mapping.values():
                if "original_path" in mapping_info:
                    mapped_files.add(mapping_info["original_path"])
                if "converted_path" in mapping_info:
                    mapped_files.add(mapping_info["converted_path"])
            
            # 清理原始文件目录
            if os.path.exists(self.originals_dir):
                for file_path in Path(self.originals_dir).glob("*"):
                    if file_path.is_file() and str(file_path) not in mapped_files:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"已清理孤立文件: {file_path}")
            
            # 清理转换文件目录
            if os.path.exists(self.converted_dir):
                for file_path in Path(self.converted_dir).glob("*"):
                    if file_path.is_file() and str(file_path) not in mapped_files:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"已清理孤立文件: {file_path}")
            
            logger.info(f"清理完成，共清理 {cleaned_count} 个孤立文件")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理孤立文件失败: {str(e)}")
            return 0
    
    def update_all_display_names(self) -> int:
        """
        更新所有现有文件映射的display_name，确保使用正确的截断逻辑
        
        Returns:
            更新的文件数量
        """
        updated_count = 0
        
        for mapping_id, mapping_info in self.file_mapping.items():
            original_filename = mapping_info.get("original_filename")
            if original_filename:
                # 重新生成display_name
                new_display_name = self._truncate_filename_for_display(original_filename)
                old_display_name = mapping_info.get("display_name", "")
                
                # 如果display_name有变化，则更新
                if new_display_name != old_display_name:
                    mapping_info["display_name"] = new_display_name
                    updated_count += 1
                    logger.info(f"更新文件映射 {mapping_id} 的display_name: '{old_display_name}' -> '{new_display_name}'")
        
        if updated_count > 0:
            # 保存更新
            self._save_mapping()
            logger.info(f"已更新 {updated_count} 个文件的display_name")
        
        return updated_count

# 全局文件存储管理器实例
file_storage_manager = FileStorageManager() 