"""
RAG核心模块 - 知识库管理器
负责整体知识库的管理和协调
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .embedder import EmbeddingManager
from .vector_store import VectorStoreManager
from .retriever import KnowledgeRetriever

# 配置路径
VECTOR_DB_PATH = "faiss_index_domain_science"
VECTOR_DB_INDEX_FILE = "faiss_index_domain_science.index"
VECTOR_DB_MAPPING_FILE = "faiss_index_domain_science_mapping.json"
TFIDF_VECTORIZER_FILE = "tfidf_vectorizer.pkl"
TFIDF_MATRIX_FILE = "tfidf_matrix.npy"
SOURCE_DOCS_PATH = "file_storage/converted"
WORKFLOW_DOCS_PATH = "file_storage/converted"

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    """知识库管理器主类"""
    
    def __init__(self):
        self.embedder = EmbeddingManager()
        self.vector_store = VectorStoreManager()
        self.retriever = KnowledgeRetriever()
        
        # 存储实例
        self.faiss_store = None
        self.tfidf_store = None
        
        # 文本分割器
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", ".", " ", ""]
        )
        
        # 初始化存储
        self._initialize_storage()
    
    def _initialize_storage(self):
        """初始化存储系统"""
        try:
            # 确保目录存在
            Path(SOURCE_DOCS_PATH).mkdir(parents=True, exist_ok=True)
            
            # 获取嵌入模型
            embedding_model = self.embedder.get_embedding_model()
            
            if embedding_model is not None:
                # 动态导入FAISS存储以避免循环导入
                from ..stores.faiss_store import FAISSStore
                
                # 使用FAISS存储
                self.faiss_store = FAISSStore(
                    self.embedder, 
                    VECTOR_DB_INDEX_FILE, 
                    VECTOR_DB_MAPPING_FILE
                )
                
                # 尝试加载现有索引
                if self.faiss_store.load_index():
                    logger.info("FAISS向量索引加载成功")
                    self.vector_store.set_primary_store(self.faiss_store)
                else:
                    logger.info("创建新的FAISS向量索引")
                    self.faiss_store.create_index()
                    self.vector_store.set_primary_store(self.faiss_store)
                    self._add_default_knowledge()
                    self.build_index_from_sources()
            else:
                # 动态导入TF-IDF存储以避免循环导入
                from ..stores.tfidf_store import TFIDFStore
                
                # 使用TF-IDF存储
                logger.info("使用TF-IDF向量化方法")
                self.tfidf_store = TFIDFStore(
                    TFIDF_VECTORIZER_FILE,
                    TFIDF_MATRIX_FILE,
                    VECTOR_DB_MAPPING_FILE
                )
                
                if self.tfidf_store.load_index():
                    logger.info("TF-IDF索引加载成功")
                    self.vector_store.set_primary_store(self.tfidf_store)
                else:
                    logger.info("创建新的TF-IDF索引")
                    self.tfidf_store.create_index()
                    self.vector_store.set_primary_store(self.tfidf_store)
                    self._add_default_knowledge()
                    self.build_index_from_sources()
                    
        except Exception as e:
            logger.error(f"初始化存储系统时出错: {str(e)}")
            # 创建TF-IDF作为备选方案
            try:
                from ..stores.tfidf_store import TFIDFStore
                self.tfidf_store = TFIDFStore(
                    TFIDF_VECTORIZER_FILE,
                    TFIDF_MATRIX_FILE,
                    VECTOR_DB_MAPPING_FILE
                )
                self.vector_store.set_primary_store(self.tfidf_store)
            except Exception as e2:
                logger.error(f"创建备选TF-IDF存储也失败: {str(e2)}")
    
    def _add_default_knowledge(self):
        """添加默认知识"""
        default_knowledge = """
=== 微波遥感基础知识 ===

微波遥感是利用微波波段的电磁波进行地表观测的技术。主要特点包括：

1. 波长范围：1mm到1m（频率300MHz-300GHz）
2. 全天候观测能力：不受云层和天气影响
3. 穿透能力：可以穿透一定厚度的植被和土壤表层

主要应用领域：
- 土壤湿度监测
- 植被参数估算  
- 地表粗糙度分析
- 海洋环境监测

常见的微波遥感参数：
- 后向散射系数（σ°）
- 土壤介电常数
- 植被含水量
- 地表粗糙度参数

=== 土壤湿度微波遥感原理 ===

土壤湿度微波遥感的基本原理基于水和土壤介电常数的显著差异：

1. 介电常数差异：
   - 干燥土壤的介电常数通常为3-5
   - 水的介电常数约为81
   - 土壤湿度的增加会显著提高土壤介电常数

2. 微波散射机理：
   - 表面散射：由地表粗糙度决定
   - 体散射：由土壤内部非均匀性决定
   - 介电常数影响散射强度

3. 反演方法：
   - 经验模型：基于统计关系
   - 半经验模型：结合物理机理
   - 物理模型：基于电磁散射理论

=== 微波散射系数与土壤参数关系 ===

后向散射系数σ°与土壤参数的关系：

1. 土壤湿度影响：
   - 湿度增加，σ°增大
   - 关系受频率和极化影响
   - 在某些条件下可能出现饱和现象

2. 地表粗糙度影响：
   - 粗糙度增加，σ°增大
   - 影响程度与频率相关
   - 需要综合考虑高度和相关长度

3. 植被覆盖影响：
   - 植被造成衰减和散射
   - 需要植被订正算法
   - 多极化数据有助于植被参数提取

注意：以上内容基于微波遥感领域的研究成果和技术发展现状。
        """
        
        logger.info("默认知识已添加到知识库")
    
    def build_index_from_sources(self):
        """从源文档构建索引"""
        try:
            # 加载所有文档
            documents = self._load_documents()
            
            if not documents:
                logger.warning("没有找到源文档")
                return
            
            # 文档分块
            chunks = []
            for doc in documents:
                doc_chunks = self.text_splitter.split_text(doc.page_content)
                for i, chunk in enumerate(doc_chunks):
                    chunks.append({
                        'text': chunk,
                        'source': doc.metadata.get('source', 'unknown'),
                        'chunk_id': f"{doc.metadata.get('source', 'unknown')}_{i}",
                        'file_mapping_id': doc.metadata.get('file_mapping_id')
                    })
            
            if not chunks:
                logger.warning("没有生成文档块")
                return
            
            # 添加到向量存储
            for chunk in chunks:
                self.vector_store.add_document(
                    chunk['text'],
                    chunk['source'],
                    chunk.get('file_mapping_id')
                )
            
            # 保存索引
            self.vector_store.save_index()
            
            logger.info(f"向量索引构建完成，包含 {len(chunks)} 个文档块")
            
        except Exception as e:
            logger.error(f"构建向量索引时出错: {str(e)}")
    
    def _load_documents(self) -> List:
        """加载所有文档"""
        from langchain.schema import Document
        
        documents = []
        source_path = Path(SOURCE_DOCS_PATH)
        
        if not source_path.exists():
            logger.warning(f"源文档目录不存在: {source_path}")
            return documents
        
        # 加载文件映射关系
        mapping_file = Path("file_storage/file_mapping.json")
        file_mapping = {}
        if mapping_file.exists():
            try:
                import json
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    file_mapping = json.load(f)
            except Exception as e:
                logger.warning(f"加载文件映射失败: {str(e)}")
        
        # 支持的文件格式
        supported_extensions = ['.txt', '.md']
        
        for file_path in source_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 从文件映射中查找原始文件名
                    file_id = file_path.stem
                    original_filename = None
                    file_mapping_id = None
                    
                    for mapping_id, mapping_info in file_mapping.items():
                        converted_path = mapping_info.get("converted_path", "")
                        if file_path.name in converted_path or file_id in converted_path:
                            original_filename = mapping_info.get("original_filename")
                            file_mapping_id = mapping_id
                            break
                    
                    if not original_filename:
                        logger.warning(f"跳过文件 {file_path.name}：未找到原始文件名映射")
                        continue
                    
                    doc = Document(
                        page_content=content,
                        metadata={
                            'source': original_filename,
                            'file_mapping_id': file_mapping_id
                        }
                    )
                    documents.append(doc)
                    logger.info(f"已加载文档: {original_filename} (来自 {file_path.name})")
                
                except Exception as e:
                    logger.warning(f"加载文档 {file_path} 时出错: {str(e)}")
        
        return documents
    
    def add_document(self, content: str, source: str = "user_upload", file_mapping_id: Optional[str] = None) -> bool:
        """添加新文档到知识库"""
        try:
            # 文档分块
            chunks = self.text_splitter.split_text(content)
            
            if not chunks:
                logger.warning("文档分块为空")
                return False
            
            # 添加到向量存储
            for i, chunk in enumerate(chunks):
                chunk_id = f"{source}_{i}"
                self.vector_store.add_document(chunk, source, file_mapping_id)
            
            # 保存索引
            self.vector_store.save_index()
            
            logger.info(f"成功添加文档到知识库，新增 {len(chunks)} 个文档块")
            return True
            
        except Exception as e:
            logger.error(f"添加文档到知识库时出错: {str(e)}")
            return False
    
    def query_knowledge(self, keywords: List[Dict[str, Any]], top_k: int = 3) -> str:
        """查询知识库"""
        return self.retriever.query_knowledge(keywords, top_k, self.vector_store)
    
    def query_knowledge_structured(self, keywords: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        """查询知识库并返回结构化结果"""
        return self.retriever.query_knowledge_structured(keywords, top_k, self.vector_store)
    
    def get_index_info(self) -> Dict[str, Any]:
        """获取索引信息"""
        return self.vector_store.get_index_info()
    
    def delete_document_by_source(self, source_name: str) -> bool:
        """根据source删除文档"""
        try:
            success = self.vector_store.delete_document_by_source(source_name)
            if success:
                self.vector_store.save_index()
            return success
        except Exception as e:
            logger.error(f"删除文档时出错: {str(e)}")
            return False
    
    def _get_default_knowledge_content(self) -> str:
        """返回默认知识内容"""
        return """
=== 微波遥感基础知识 ===

微波遥感是利用微波波段的电磁波进行地表观测的技术。主要特点包括：

1. 波长范围：1mm到1m（频率300MHz-300GHz）
2. 全天候观测能力：不受云层和天气影响
3. 穿透能力：可以穿透一定厚度的植被和土壤表层

主要应用领域：
- 土壤湿度监测
- 植被参数估算  
- 地表粗糙度分析
- 海洋环境监测

常见的微波遥感参数：
- 后向散射系数（σ°）
- 土壤介电常数
- 植被含水量
- 地表粗糙度参数

注意：这是默认知识内容，建议上传更多专业文档以获得更准确的信息。
        """
    
    # === 向后兼容属性 ===
    # 这些属性为了保持与旧代码的兼容性
    
    @property
    def faiss_index(self):
        """获取FAISS索引（向后兼容）"""
        if self.faiss_store and hasattr(self.faiss_store, 'faiss_index'):
            return self.faiss_store.faiss_index
        return None
    
    @property
    def use_sentence_transformers(self):
        """是否使用SentenceTransformers（向后兼容）"""
        return self.embedder.is_available()
    
    @property
    def documents_texts(self):
        """获取文档文本列表（向后兼容）"""
        # 尝试从向量存储中获取文档信息
        try:
            index_info = self.get_index_info()
            # 返回空列表，因为新架构中不再直接存储文档文本
            return []
        except:
            return []
    
    @property
    def doc_mapping(self):
        """获取文档映射（向后兼容）"""
        # 尝试从向量存储中获取文档映射
        try:
            if self.faiss_store and hasattr(self.faiss_store, 'doc_mapping'):
                return self.faiss_store.doc_mapping
            elif self.tfidf_store and hasattr(self.tfidf_store, 'doc_mapping'):
                return self.tfidf_store.doc_mapping
            return {}
        except:
            return {}
    
    @property
    def tfidf_matrix(self):
        """获取TF-IDF矩阵（向后兼容）"""
        if self.tfidf_store and hasattr(self.tfidf_store, 'tfidf_matrix'):
            return self.tfidf_store.tfidf_matrix
        return None
    
    def get_total_documents(self) -> int:
        """获取文档总数（向后兼容）"""
        try:
            index_info = self.get_index_info()
            return index_info.get('total_documents', 0)
        except:
            return 0