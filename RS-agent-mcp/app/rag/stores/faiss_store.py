"""
RAG存储模块 - FAISS向量存储实现
使用FAISS进行高效的向量相似度搜索
"""

import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from ..core.vector_store import BaseVectorStore
from ..core.embedder import EmbeddingManager

logger = logging.getLogger(__name__)


class FAISSStore(BaseVectorStore):
    """FAISS向量存储实现"""
    
    def __init__(self, embedding_manager: EmbeddingManager, index_file: str, mapping_file: str):
        self.embedding_manager = embedding_manager
        self.index_file = index_file
        self.mapping_file = mapping_file
        self.faiss_index = None
        self.doc_mapping = {}
        self.embedding_dim = None
    
    def load_index(self) -> bool:
        """加载FAISS索引"""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS不可用")
            return False
        
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.mapping_file):
                logger.info("加载现有FAISS向量索引...")
                self.faiss_index = faiss.read_index(self.index_file)
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.doc_mapping = json.load(f)
                
                # 获取嵌入维度
                if self.faiss_index.ntotal > 0:
                    self.embedding_dim = self.faiss_index.d
                
                logger.info(f"成功加载FAISS向量索引，包含 {self.faiss_index.ntotal} 个文档片段")
                return True
            else:
                logger.info("FAISS索引文件不存在，需要创建新索引")
                return False
                
        except Exception as e:
            logger.error(f"加载FAISS索引时出错: {str(e)}")
            return False
    
    def create_index(self) -> bool:
        """创建新的FAISS索引"""
        if not FAISS_AVAILABLE:
            logger.warning("FAISS不可用，无法创建索引")
            return False
        
        try:
            # 获取嵌入模型
            embedding_model = self.embedding_manager.get_embedding_model()
            if embedding_model is None:
                logger.error("嵌入模型不可用，无法创建FAISS索引")
                return False
            
            # 获取嵌入维度
            self.embedding_dim = embedding_model.get_sentence_embedding_dimension()
            
            # 创建FAISS索引
            self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)  # 使用内积相似度
            self.doc_mapping = {}
            
            logger.info(f"创建新的FAISS索引，嵌入维度: {self.embedding_dim}")
            return True
            
        except Exception as e:
            logger.error(f"创建FAISS索引时出错: {str(e)}")
            return False
    
    def save_index(self) -> bool:
        """保存FAISS索引"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            logger.warning("FAISS索引不可用，无法保存")
            return False
        
        try:
            # 保存FAISS索引
            faiss.write_index(self.faiss_index, self.index_file)
            
            # 保存文档映射
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.doc_mapping, f, ensure_ascii=False, indent=2)
            
            logger.info("FAISS向量索引和映射已保存")
            return True
            
        except Exception as e:
            logger.error(f"保存FAISS索引时出错: {str(e)}")
            return False
    
    def add_document(self, content: str, source: str, file_mapping_id: Optional[str] = None) -> bool:
        """添加文档到FAISS索引"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            logger.warning("FAISS索引不可用")
            return False
        
        try:
            # 生成嵌入向量
            embeddings = self.embedding_manager.encode_texts([content])
            if embeddings is None:
                logger.error("生成嵌入向量失败")
                return False
            
            # 添加到索引
            start_idx = self.faiss_index.ntotal
            self.faiss_index.add(embeddings)
            
            # 更新文档映射
            chunk_id = str(start_idx)
            self.doc_mapping[chunk_id] = {
                'text': content,
                'source': source,
                'chunk_id': f"{source}_{start_idx}",
                'file_mapping_id': file_mapping_id
            }
            
            logger.debug(f"成功添加文档到FAISS索引，索引: {start_idx}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档到FAISS索引时出错: {str(e)}")
            return False
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """查询FAISS索引"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            logger.warning("FAISS索引不可用")
            return []
        
        try:
            if self.faiss_index.ntotal == 0:
                logger.warning("FAISS索引为空")
                return []
            
            # 生成查询嵌入向量
            query_embedding = self.embedding_manager.encode_query(query_text)
            if query_embedding is None:
                logger.error("生成查询向量失败")
                return []
            
            # 搜索相似文档
            scores, indices = self.faiss_index.search(query_embedding, top_k)
            
            # 获取相关文档
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx != -1 and str(idx) in self.doc_mapping:
                    doc_info = self.doc_mapping[str(idx)]
                    result = {
                        'content': doc_info['text'],
                        'source': doc_info['source'],
                        'similarity': float(score)
                    }
                    
                    # 添加文件映射信息
                    if 'file_mapping_id' in doc_info and doc_info['file_mapping_id']:
                        result['file_mapping_id'] = doc_info['file_mapping_id']
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"查询FAISS索引时出错: {str(e)}")
            return []
    
    def delete_document_by_source(self, source_name: str) -> bool:
        """根据source删除文档"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            logger.warning("FAISS索引不可用")
            return False
        
        try:
            if self.faiss_index.ntotal == 0:
                logger.warning("FAISS索引为空，无法删除文档")
                return False
            
            # 找到要删除的文档块
            indices_to_delete = []
            remaining_mapping = {}
            
            for idx_str, doc_info in self.doc_mapping.items():
                if doc_info['source'] == source_name:
                    indices_to_delete.append(int(idx_str))
                else:
                    remaining_mapping[idx_str] = doc_info
            
            if not indices_to_delete:
                logger.warning(f"未找到source为 {source_name} 的文档")
                return False
            
            # 由于FAISS不支持直接删除特定索引，我们需要重建索引
            logger.info(f"找到 {len(indices_to_delete)} 个文档块需要删除，重建FAISS索引...")
            
            # 保存未删除的文档
            remaining_docs = []
            
            for idx_str, doc_info in remaining_mapping.items():
                remaining_docs.append(doc_info)
            
            if not remaining_docs:
                # 如果没有剩余文档，创建空索引
                if not self.create_index():
                    return False
            else:
                # 重新创建索引
                remaining_texts = [doc['text'] for doc in remaining_docs]
                embeddings = self.embedding_manager.encode_texts(remaining_texts)
                
                if embeddings is None:
                    logger.error("重新生成嵌入向量失败")
                    return False
                
                # 重新创建FAISS索引
                self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
                self.faiss_index.add(embeddings)
                
                # 重建映射
                self.doc_mapping = {}
                for i, doc_info in enumerate(remaining_docs):
                    self.doc_mapping[str(i)] = {
                        'text': doc_info['text'],
                        'source': doc_info['source'],
                        'chunk_id': doc_info.get('chunk_id', f"{doc_info['source']}_{i}"),
                        'file_mapping_id': doc_info.get('file_mapping_id')
                    }
            
            logger.info(f"成功删除source为 {source_name} 的文档，删除了 {len(indices_to_delete)} 个文档块")
            return True
            
        except Exception as e:
            logger.error(f"使用FAISS删除文档时出错: {str(e)}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取FAISS索引信息"""
        return {
            'total_documents': self.faiss_index.ntotal if self.faiss_index else 0,
            'store_type': 'FAISS',
            'embedding_dimension': self.embedding_dim,
            'index_file': self.index_file,
            'mapping_file': self.mapping_file,
            'status': 'available' if self.faiss_index else 'unavailable'
        }
    
    def get_total_documents(self) -> int:
        """获取文档总数"""
        return self.faiss_index.ntotal if self.faiss_index else 0
    
    def is_available(self) -> bool:
        """检查FAISS是否可用"""
        return FAISS_AVAILABLE and self.faiss_index is not None
    
    def optimize_index(self):
        """优化FAISS索引（可选）"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return
        
        try:
            # 可以在这里添加索引优化逻辑，比如使用更高效的索引类型
            logger.info("FAISS索引优化（当前使用FlatIP索引）")
        except Exception as e:
            logger.error(f"优化FAISS索引时出错: {str(e)}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return {'available': False}
        
        try:
            import psutil
            import os
            
            # 获取索引文件大小
            index_size = os.path.getsize(self.index_file) if os.path.exists(self.index_file) else 0
            mapping_size = os.path.getsize(self.mapping_file) if os.path.exists(self.mapping_file) else 0
            
            # 估算内存使用
            memory_usage = self.faiss_index.ntotal * self.embedding_dim * 4  # 假设float32类型
            
            return {
                'available': True,
                'total_documents': self.faiss_index.ntotal,
                'embedding_dimension': self.embedding_dim,
                'index_file_size_mb': index_size / (1024 * 1024),
                'mapping_file_size_mb': mapping_size / (1024 * 1024),
                'estimated_memory_mb': memory_usage / (1024 * 1024)
            }
            
        except Exception as e:
            logger.error(f"获取内存使用情况时出错: {str(e)}")
            return {'available': False, 'error': str(e)}