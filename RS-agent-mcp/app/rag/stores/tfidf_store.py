"""
RAG存储模块 - TF-IDF向量存储实现
使用TF-IDF作为FAISS的备选方案
"""

import os
import json
import pickle
import logging
import numpy as np
from typing import List, Dict, Any, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ..core.vector_store import BaseVectorStore

logger = logging.getLogger(__name__)


class TFIDFStore(BaseVectorStore):
    """TF-IDF向量存储实现"""
    
    def __init__(self, vectorizer_file: str, matrix_file: str, mapping_file: str):
        self.vectorizer_file = vectorizer_file
        self.matrix_file = matrix_file
        self.mapping_file = mapping_file
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.documents_texts = []
        self.doc_mapping = {}
    
    def load_index(self) -> bool:
        """加载TF-IDF索引"""
        try:
            if (os.path.exists(self.vectorizer_file) and 
                os.path.exists(self.matrix_file) and 
                os.path.exists(self.mapping_file)):
                
                logger.info("加载现有TF-IDF索引...")
                
                # 加载向量化器
                with open(self.vectorizer_file, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
                
                # 加载矩阵
                self.tfidf_matrix = np.load(self.matrix_file, allow_pickle=True)
                
                # 加载文档映射
                with open(self.mapping_file, 'r', encoding='utf-8') as f:
                    self.doc_mapping = json.load(f)
                
                # 重建文档文本列表
                self.documents_texts = [self.doc_mapping[str(i)]['text'] 
                                       for i in range(len(self.doc_mapping))]
                
                logger.info(f"成功加载TF-IDF索引，包含 {len(self.documents_texts)} 个文档片段")
                return True
            else:
                logger.info("TF-IDF索引文件不存在，需要创建新索引")
                return False
                
        except Exception as e:
            logger.error(f"加载TF-IDF索引时出错: {str(e)}")
            return False
    
    def create_index(self) -> bool:
        """创建新的TF-IDF索引"""
        try:
            # 初始化TF-IDF向量化器
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words=None,  # 不使用英文停用词，保留中文
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95
            )
            
            # 重置数据
            self.tfidf_matrix = None
            self.documents_texts = []
            self.doc_mapping = {}
            
            logger.info("创建新的TF-IDF索引")
            return True
            
        except Exception as e:
            logger.error(f"创建TF-IDF索引时出错: {str(e)}")
            return False
    
    def save_index(self) -> bool:
        """保存TF-IDF索引"""
        try:
            # 保存TF-IDF向量化器
            with open(self.vectorizer_file, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            
            # 保存TF-IDF矩阵（处理空矩阵的情况）
            if self.tfidf_matrix is not None:
                np.save(self.matrix_file, self.tfidf_matrix.toarray())
            else:
                # 保存空矩阵
                np.save(self.matrix_file, np.array([]))
            
            # 保存文档映射
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.doc_mapping, f, ensure_ascii=False, indent=2)
            
            logger.info("TF-IDF索引已保存")
            return True
            
        except Exception as e:
            logger.error(f"保存TF-IDF索引时出错: {str(e)}")
            return False
    
    def add_document(self, content: str, source: str, file_mapping_id: Optional[str] = None) -> bool:
        """添加文档到TF-IDF索引"""
        try:
            # 添加到文档列表
            start_idx = len(self.documents_texts)
            self.documents_texts.append(content)
            
            # 重新训练TF-IDF向量化器
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents_texts)
            
            # 更新文档映射
            chunk_id = str(start_idx)
            self.doc_mapping[chunk_id] = {
                'text': content,
                'source': source,
                'chunk_id': f"{source}_{start_idx}",
                'file_mapping_id': file_mapping_id
            }
            
            logger.debug(f"成功添加文档到TF-IDF索引，索引: {start_idx}")
            return True
            
        except Exception as e:
            logger.error(f"添加文档到TF-IDF索引时出错: {str(e)}")
            return False
    
    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """查询TF-IDF索引"""
        try:
            if not self.documents_texts or self.tfidf_matrix is None:
                logger.warning("TF-IDF索引为空")
                return []
            
            # 将查询文本转换为TF-IDF向量
            query_vector = self.tfidf_vectorizer.transform([query_text])
            
            # 计算相似度
            similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
            
            # 获取最相似的文档索引
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # 获取相关文档
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # 只返回相似度大于0.1的结果
                    if str(idx) in self.doc_mapping:
                        doc_info = self.doc_mapping[str(idx)]
                        result = {
                            'content': doc_info['text'],
                            'source': doc_info['source'],
                            'similarity': float(similarities[idx])
                        }
                        
                        # 添加文件映射信息
                        if 'file_mapping_id' in doc_info and doc_info['file_mapping_id']:
                            result['file_mapping_id'] = doc_info['file_mapping_id']
                        
                        results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"查询TF-IDF索引时出错: {str(e)}")
            return []
    
    def delete_document_by_source(self, source_name: str) -> bool:
        """根据source删除文档"""
        try:
            if not self.documents_texts or not self.doc_mapping:
                logger.warning("TF-IDF索引为空，无法删除文档")
                return False
            
            # 找到要删除的文档块
            indices_to_delete = []
            for idx_str, doc_info in self.doc_mapping.items():
                if doc_info['source'] == source_name:
                    indices_to_delete.append(int(idx_str))
            
            if not indices_to_delete:
                logger.warning(f"未找到source为 {source_name} 的文档")
                return False
            
            # 删除文档文本和映射
            indices_to_delete.sort(reverse=True)  # 从后往前删除，避免索引变化
            
            for idx in indices_to_delete:
                if idx < len(self.documents_texts):
                    del self.documents_texts[idx]
                if str(idx) in self.doc_mapping:
                    del self.doc_mapping[str(idx)]
            
            # 重新编号映射
            new_mapping = {}
            new_texts = []
            idx = 0
            
            for text in self.documents_texts:
                # 从原映射中找到对应的source信息
                for old_idx_str, doc_info in self.doc_mapping.items():
                    if doc_info['text'] == text:
                        new_mapping[str(idx)] = {
                            'text': text,
                            'source': doc_info['source'],
                            'chunk_id': doc_info.get('chunk_id', f"{doc_info['source']}_{idx}"),
                            'file_mapping_id': doc_info.get('file_mapping_id')
                        }
                        new_texts.append(text)
                        idx += 1
                        break
            
            self.documents_texts = new_texts
            self.doc_mapping = new_mapping
            
            # 重新训练TF-IDF向量化器
            if self.documents_texts:
                self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.documents_texts)
            else:
                self.tfidf_matrix = None
            
            logger.info(f"成功删除source为 {source_name} 的文档，删除了 {len(indices_to_delete)} 个文档块")
            return True
            
        except Exception as e:
            logger.error(f"使用TF-IDF删除文档时出错: {str(e)}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取TF-IDF索引信息"""
        return {
            'total_documents': len(self.documents_texts),
            'store_type': 'TF-IDF',
            'vectorizer_file': self.vectorizer_file,
            'matrix_file': self.matrix_file,
            'mapping_file': self.mapping_file,
            'status': 'available' if self.documents_texts else 'empty'
        }
    
    def get_total_documents(self) -> int:
        """获取文档总数"""
        return len(self.documents_texts)
    
    def is_available(self) -> bool:
        """检查TF-IDF是否可用"""
        return self.tfidf_vectorizer is not None
    
    def get_vocabulary_info(self) -> Dict[str, Any]:
        """获取词汇表信息"""
        if not self.tfidf_vectorizer:
            return {'available': False}
        
        try:
            vocabulary = self.tfidf_vectorizer.vocabulary_
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            return {
                'available': True,
                'vocabulary_size': len(vocabulary),
                'max_features': self.tfidf_vectorizer.max_features,
                'ngram_range': self.tfidf_vectorizer.ngram_range,
                'sample_features': list(feature_names[:10])  # 显示前10个特征
            }
            
        except Exception as e:
            logger.error(f"获取词汇表信息时出错: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def get_document_statistics(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        if not self.documents_texts:
            return {'available': False}
        
        try:
            # 计算文档长度统计
            doc_lengths = [len(doc) for doc in self.documents_texts]
            
            # 计算平均词数（简单分词）
            word_counts = []
            for doc in self.documents_texts:
                words = doc.split()
                word_counts.append(len(words))
            
            return {
                'available': True,
                'total_documents': len(self.documents_texts),
                'total_characters': sum(doc_lengths),
                'average_document_length': np.mean(doc_lengths),
                'max_document_length': max(doc_lengths),
                'min_document_length': min(doc_lengths),
                'total_words': sum(word_counts),
                'average_words_per_document': np.mean(word_counts),
                'max_words_per_document': max(word_counts),
                'min_words_per_document': min(word_counts)
            }
            
        except Exception as e:
            logger.error(f"获取文档统计信息时出错: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def rebuild_index_with_new_params(self, max_features: int = None, ngram_range: tuple = None):
        """使用新参数重建索引"""
        try:
            # 保存当前文档
            current_docs = self.documents_texts.copy()
            current_mapping = self.doc_mapping.copy()
            
            # 更新向量化器参数
            if max_features is not None:
                self.tfidf_vectorizer.max_features = max_features
            if ngram_range is not None:
                self.tfidf_vectorizer.ngram_range = ngram_range
            
            # 重新创建索引
            self.documents_texts = []
            self.doc_mapping = {}
            self.tfidf_matrix = None
            
            # 重新添加文档
            for i, doc_text in enumerate(current_docs):
                doc_info = current_mapping.get(str(i), {})
                source = doc_info.get('source', f'document_{i}')
                file_mapping_id = doc_info.get('file_mapping_id')
                
                self.add_document(doc_text, source, file_mapping_id)
            
            logger.info("TF-IDF索引已使用新参数重建")
            return True
            
        except Exception as e:
            logger.error(f"重建TF-IDF索引时出错: {str(e)}")
            return False
    
    def get_feature_importance(self, text: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """获取文本中最重要的特征词"""
        if not self.tfidf_vectorizer:
            return []
        
        try:
            # 转换文本为TF-IDF向量
            tfidf_vector = self.tfidf_vectorizer.transform([text])
            
            # 获取特征名称
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # 获取特征值
            feature_values = tfidf_vector.toarray()[0]
            
            # 获取非零特征
            non_zero_indices = feature_values.nonzero()[0]
            
            # 按重要性排序
            feature_importance = []
            for idx in non_zero_indices:
                feature_importance.append({
                    'feature': feature_names[idx],
                    'score': float(feature_values[idx])
                })
            
            feature_importance.sort(key=lambda x: x['score'], reverse=True)
            
            return feature_importance[:top_n]
            
        except Exception as e:
            logger.error(f"获取特征重要性时出错: {str(e)}")
            return []