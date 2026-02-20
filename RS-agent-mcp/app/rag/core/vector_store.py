"""
RAG核心模块 - 向量存储管理器
提供向量存储的统一抽象接口
"""

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    """向量存储抽象基类"""
    
    @abstractmethod
    def load_index(self) -> bool:
        """加载索引"""
        pass
    
    @abstractmethod
    def create_index(self) -> bool:
        """创建索引"""
        pass
    
    @abstractmethod
    def save_index(self) -> bool:
        """保存索引"""
        pass
    
    @abstractmethod
    def add_document(self, content: str, source: str, file_mapping_id: Optional[str] = None) -> bool:
        """添加文档"""
        pass
    
    @abstractmethod
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """查询文档"""
        pass
    
    @abstractmethod
    def delete_document_by_source(self, source_name: str) -> bool:
        """根据source删除文档"""
        pass
    
    @abstractmethod
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        pass
    
    @abstractmethod
    def get_total_documents(self) -> int:
        """获取文档总数"""
        pass


class VectorStoreManager:
    """向量存储管理器"""
    
    def __init__(self):
        self.primary_store: Optional[BaseVectorStore] = None
        self.fallback_store: Optional[BaseVectorStore] = None
    
    def set_primary_store(self, store: BaseVectorStore):
        """设置主存储"""
        self.primary_store = store
        logger.info(f"设置主存储: {type(store).__name__}")
    
    def set_fallback_store(self, store: BaseVectorStore):
        """设置备选存储"""
        self.fallback_store = store
        logger.info(f"设置备选存储: {type(store).__name__}")
    
    def add_document(self, content: str, source: str, file_mapping_id: Optional[str] = None) -> bool:
        """添加文档"""
        if self.primary_store:
            return self.primary_store.add_document(content, source, file_mapping_id)
        elif self.fallback_store:
            return self.fallback_store.add_document(content, source, file_mapping_id)
        else:
            logger.error("没有可用的向量存储")
            return False
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """查询文档"""
        if self.primary_store:
            return self.primary_store.query(query_text, top_k)
        elif self.fallback_store:
            return self.fallback_store.query(query_text, top_k)
        else:
            logger.error("没有可用的向量存储")
            return []
    
    def delete_document_by_source(self, source_name: str) -> bool:
        """根据source删除文档"""
        if self.primary_store:
            return self.primary_store.delete_document_by_source(source_name)
        elif self.fallback_store:
            return self.fallback_store.delete_document_by_source(source_name)
        else:
            logger.error("没有可用的向量存储")
            return False
    
    def save_index(self) -> bool:
        """保存索引"""
        if self.primary_store:
            return self.primary_store.save_index()
        elif self.fallback_store:
            return self.fallback_store.save_index()
        else:
            logger.error("没有可用的向量存储")
            return False
    
    def load_index(self) -> bool:
        """加载索引"""
        if self.primary_store:
            return self.primary_store.load_index()
        elif self.fallback_store:
            return self.fallback_store.load_index()
        else:
            logger.error("没有可用的向量存储")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        if self.primary_store:
            return self.primary_store.get_index_info()
        elif self.fallback_store:
            return self.fallback_store.get_index_info()
        else:
            return {
                'total_documents': 0,
                'store_type': 'none',
                'status': 'no_store_available'
            }
    
    def get_total_documents(self) -> int:
        """获取文档总数"""
        if self.primary_store:
            return self.primary_store.get_total_documents()
        elif self.fallback_store:
            return self.fallback_store.get_total_documents()
        else:
            return 0
    
    def is_available(self) -> bool:
        """检查存储是否可用"""
        return self.primary_store is not None or self.fallback_store is not None
    
    def get_store_type(self) -> str:
        """获取存储类型"""
        if self.primary_store:
            return type(self.primary_store).__name__
        elif self.fallback_store:
            return type(self.fallback_store).__name__
        else:
            return 'none'
    
    def rebuild_index(self):
        """重建索引"""
        logger.info("开始重建向量索引...")
        
        if self.primary_store:
            try:
                # 获取当前所有文档
                current_docs = []
                if hasattr(self.primary_store, 'doc_mapping'):
                    for doc_info in self.primary_store.doc_mapping.values():
                        current_docs.append({
                            'text': doc_info['text'],
                            'source': doc_info['source'],
                            'file_mapping_id': doc_info.get('file_mapping_id')
                        })
                
                # 重新创建索引
                self.primary_store.create_index()
                
                # 重新添加文档
                for doc in current_docs:
                    self.primary_store.add_document(doc['text'], doc['source'], doc.get('file_mapping_id'))
                
                # 保存索引
                self.primary_store.save_index()
                
                logger.info(f"索引重建完成，包含 {len(current_docs)} 个文档")
                return True
                
            except Exception as e:
                logger.error(f"重建主存储索引失败: {str(e)}")
                return False
        else:
            logger.warning("没有主存储，无法重建索引")
            return False