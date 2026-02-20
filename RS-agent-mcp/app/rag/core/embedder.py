"""
RAG核心模块 - 嵌入模型管理器
负责嵌入模型的加载、管理和向量生成
"""

import os
import logging
import numpy as np
from typing import Optional, List

# 尝试导入高级嵌入模型，如果失败则使用TF-IDF备选方案
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

# 模型名称配置
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
from app.core.config import settings

class EmbeddingManager:
    """嵌入模型管理器"""
    
    def __init__(self):
        self.embedding_model = None
        self.embedding_path = settings.EMBEDDING_PATH
        self.use_sentence_transformers = False
        self.embedding_dim = None
    
    def get_embedding_model(self):
        """获取嵌入模型"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("SentenceTransformers不可用，将使用TF-IDF方法")
            return None
            
        if self.embedding_model is None:
            try:
                logger.info("尝试加载嵌入模型...")
                
                # 按优先级排序的模型列表（从小到大，从稳定到实验）
                model_names = [
                    # 优先使用小型、稳定的模型
                    "all-MiniLM-L6-v2",  # 22MB，英文，速度快，稳定
                    "paraphrase-MiniLM-L6-v2",  # 22MB，英文，备选
                    
                    # 多语言支持模型
                    "paraphrase-multilingual-MiniLM-L12-v2",  # 多语言
                    "distiluse-base-multilingual-cased",  # 多语言备选
                    
                    # 更大的模型（如果前面的都失败）
                    "all-MiniLM-L12-v2",  # 稍大但效果更好
                ]
                
                for model_name in model_names:
                    try:
                        logger.info(f"尝试加载模型: {model_name}")
                        
                        # 强制离线模式，避免网络连接
                        original_offline = os.environ.get('HF_HUB_OFFLINE', None)
                        original_disable_telemetry = os.environ.get('HF_HUB_DISABLE_TELEMETRY', None)
                        
                        try:
                            # 强制离线模式
                            os.environ['HF_HUB_OFFLINE'] = '1'
                            os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
                            
                            # 设置较短的超时时间
                            import socket
                            original_timeout = socket.getdefaulttimeout()
                            socket.setdefaulttimeout(10)  # 10秒超时
                            
                            try:
                                # 尝试加载本地缓存的模型
                                # 如果设置了embedding_path，使用自定义路径，否则使用模型名称（自动从HuggingFace缓存加载）
                                model_path = f"{self.embedding_path}/{model_name}" if self.embedding_path else model_name
                                self.embedding_model = SentenceTransformer(
                                    model_path,
                                    local_files_only=True  # 强制只使用本地文件
                                )
                                self.use_sentence_transformers = True
                                logger.info(f"✓ 成功从本地缓存加载嵌入模型: {model_name}")
                                
                                # 测试模型是否正常工作
                                test_embedding = self.embedding_model.encode("测试文本")
                                self.embedding_dim = len(test_embedding)
                                logger.info(f"✓ 模型测试通过，嵌入维度: {self.embedding_dim}")
                                break
                                
                            except Exception as local_e:
                                logger.warning(f"本地加载失败: {str(local_e)}")
                                
                                # 如果本地加载失败，尝试联网加载（但设置较短超时）
                                logger.info(f"尝试联网加载模型: {model_name}")
                                os.environ['HF_HUB_OFFLINE'] = '0'
                                
                                # 如果设置了embedding_path，使用自定义路径，否则使用模型名称
                                model_path = f"{self.embedding_path}/{model_name}" if self.embedding_path else model_name
                                self.embedding_model = SentenceTransformer(model_path)
                                self.use_sentence_transformers = True
                                logger.info(f"✓ 成功联网加载嵌入模型: {model_name}")
                                
                                # 测试模型是否正常工作
                                test_embedding = self.embedding_model.encode("测试文本")
                                self.embedding_dim = len(test_embedding)
                                logger.info(f"✓ 模型测试通过，嵌入维度: {self.embedding_dim}")
                                break
                                
                            finally:
                                socket.setdefaulttimeout(original_timeout)
                            
                        finally:
                            # 恢复原始环境变量
                            if original_offline is not None:
                                os.environ['HF_HUB_OFFLINE'] = original_offline
                            else:
                                os.environ.pop('HF_HUB_OFFLINE', None)
                                
                            if original_disable_telemetry is not None:
                                os.environ['HF_HUB_DISABLE_TELEMETRY'] = original_disable_telemetry
                            else:
                                os.environ.pop('HF_HUB_DISABLE_TELEMETRY', None)
                            
                    except Exception as e:
                        logger.warning(f"✗ 加载模型 {model_name} 失败: {str(e)}")
                        # 如果是网络连接错误，给出更详细的提示
                        if "Connection" in str(e) or "timeout" in str(e).lower() or "offline" in str(e).lower():
                            logger.warning(f"  网络连接问题或缺少本地缓存，可以尝试运行 'python download_models.py' 重新下载模型")
                        continue
                
                if self.embedding_model is None:
                    logger.warning("所有嵌入模型加载失败，将使用TF-IDF方法")
                    logger.info("提示：可以运行 'python download_models.py' 预下载模型到本地缓存")
                    self.use_sentence_transformers = False
                    
            except Exception as e:
                logger.warning(f"嵌入模型加载失败: {str(e)}，将使用TF-IDF方法")
                self.use_sentence_transformers = False
                
        return self.embedding_model
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> Optional[np.ndarray]:
        """将文本列表编码为向量"""
        if not self.use_sentence_transformers or self.embedding_model is None:
            logger.warning("嵌入模型不可用")
            return None
        
        try:
            logger.info(f"正在生成 {len(texts)} 个文本的嵌入向量...")
            embeddings = self.embedding_model.encode(texts, batch_size=batch_size, show_progress_bar=True)
            
            # 标准化嵌入向量（用于内积相似度）
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            return embeddings.astype('float32')
            
        except Exception as e:
            logger.error(f"生成嵌入向量时出错: {str(e)}")
            return None
    
    def encode_query(self, query_text: str) -> Optional[np.ndarray]:
        """将查询文本编码为向量"""
        if not self.use_sentence_transformers or self.embedding_model is None:
            logger.warning("嵌入模型不可用")
            return None
        
        try:
            # 生成查询嵌入向量
            query_embedding = self.embedding_model.encode([query_text])
            
            # 标准化查询向量
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            return query_embedding.astype('float32')
            
        except Exception as e:
            logger.error(f"生成查询向量时出错: {str(e)}")
            return None
    
    def get_embedding_dimension(self) -> Optional[int]:
        """获取嵌入维度"""
        return self.embedding_dim
    
    def is_available(self) -> bool:
        """检查嵌入模型是否可用"""
        return self.use_sentence_transformers and self.embedding_model is not None
    
    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            'available': self.is_available(),
            'use_sentence_transformers': self.use_sentence_transformers,
            'embedding_dimension': self.embedding_dim,
            'model_name': EMBEDDING_MODEL_NAME if self.use_sentence_transformers else 'TF-IDF'
        }