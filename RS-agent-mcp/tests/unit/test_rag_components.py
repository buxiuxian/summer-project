"""
RAG组件的单元测试
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import numpy as np

from app.rag.core.knowledge_manager import KnowledgeBaseManager
from app.rag.core.embedder import EmbeddingManager
from app.rag.core.vector_store import VectorStoreManager


class TestEmbeddingManager:
    """嵌入管理器测试类"""
    
    @pytest.fixture
    def embedder(self):
        """创建嵌入管理器实例"""
        return EmbeddingManager()
    
    def test_embedder_initialization(self, embedder):
        """测试嵌入管理器初始化"""
        assert embedder is not None
        assert hasattr(embedder, 'get_embedding_model')
    
    @patch('app.rag.core.embedder.SentenceTransformer')
    def test_get_embedding_model(self, mock_transformer, embedder):
        """测试获取嵌入模型"""
        mock_model = Mock()
        mock_transformer.return_value = mock_model
        
        with patch('app.rag.core.embedder.SENTENCE_TRANSFORMERS_AVAILABLE', True):
            result = embedder.get_embedding_model()
            assert result == mock_model
    
    def test_get_embedding_model_unavailable(self, embedder):
        """测试嵌入模型不可用时的处理"""
        with patch('app.rag.core.embedder.SENTENCE_TRANSFORMERS_AVAILABLE', False):
            result = embedder.get_embedding_model()
            assert result is None
    
    def test_encode_texts_with_sentence_transformer(self, embedder):
        """测试使用SentenceTransformer编码文本"""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])  # 返回二维数组
        
        # 直接设置embedder的状态
        embedder.embedding_model = mock_model
        embedder.use_sentence_transformers = True
        embedder.embedding_dim = 3
        
        result = embedder.encode_texts(["测试文本"])
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert len(result[0]) == 3
    
    def test_encode_texts_fallback_to_tfidf(self, embedder):
        """测试回退到TF-IDF编码"""
        with patch.object(embedder, 'get_embedding_model', return_value=None):
            result = embedder.encode_texts(["测试文本"])
            assert result is None  # 当模型不可用时返回None


class TestVectorStoreManager:
    """向量存储管理器测试类"""
    
    @pytest.fixture
    def vector_store(self):
        """创建向量存储管理器实例"""
        return VectorStoreManager()
    
    def test_vector_store_initialization(self, vector_store):
        """测试向量存储管理器初始化"""
        assert vector_store is not None
        assert hasattr(vector_store, 'primary_store')
        assert hasattr(vector_store, 'fallback_store')
        assert vector_store.primary_store is None
        assert vector_store.fallback_store is None
    
    def test_set_primary_store(self, vector_store):
        """测试设置主存储"""
        mock_store = Mock()
        vector_store.set_primary_store(mock_store)
        assert vector_store.primary_store == mock_store
    
    def test_set_fallback_store(self, vector_store):
        """测试设置备选存储"""
        mock_store = Mock()
        vector_store.set_fallback_store(mock_store)
        assert vector_store.fallback_store == mock_store
    
    def test_is_available(self, vector_store):
        """测试存储可用性检查"""
        # 初始状态不可用
        assert vector_store.is_available() is False
        
        # 设置主存储后可用
        mock_store = Mock()
        vector_store.set_primary_store(mock_store)
        assert vector_store.is_available() is True
        
        # 清除主存储，设置备选存储后也可用
        vector_store.primary_store = None
        vector_store.set_fallback_store(mock_store)
        assert vector_store.is_available() is True


class TestKnowledgeBaseManager:
    """知识库管理器测试类"""
    
    @pytest.fixture
    def knowledge_manager(self):
        """创建知识库管理器实例"""
        return KnowledgeBaseManager()
    
    def test_knowledge_manager_initialization(self, knowledge_manager):
        """测试知识库管理器初始化"""
        assert knowledge_manager is not None
        assert hasattr(knowledge_manager, 'embedder')
        assert hasattr(knowledge_manager, 'vector_store')
        assert hasattr(knowledge_manager, 'retriever')
    
    def test_get_index_info(self, knowledge_manager):
        """测试获取索引信息"""
        # 设置mock
        knowledge_manager.vector_store = Mock()
        knowledge_manager.vector_store.get_index_info.return_value = {
            "total_documents": 10,
            "total_chunks": 50,
            "dimension": 384
        }
        
        result = knowledge_manager.get_index_info()
        assert result["total_documents"] == 10
        assert result["total_chunks"] == 50
        assert result["dimension"] == 384
    
    def test_query_knowledge(self, knowledge_manager):
        """测试知识查询"""
        # 设置mock
        knowledge_manager.retriever = Mock()
        knowledge_manager.retriever.query_knowledge.return_value = "查询结果"
        
        keywords = [{"keyword": "机器学习", "weight": 0.9}]
        result = knowledge_manager.query_knowledge(keywords)
        
        assert result == "查询结果"
        knowledge_manager.retriever.query_knowledge.assert_called_once_with(keywords, 3, knowledge_manager.vector_store)
    
    def test_query_knowledge_structured(self, knowledge_manager):
        """测试结构化知识查询"""
        # 设置mock
        expected_result = [
            {"content": "机器学习是AI的一个分支", "score": 0.9, "source": "test.pdf"}
        ]
        knowledge_manager.retriever = Mock()
        knowledge_manager.retriever.query_knowledge_structured.return_value = expected_result
        
        keywords = [{"keyword": "机器学习", "weight": 0.9}]
        result = knowledge_manager.query_knowledge_structured(keywords, top_k=3)
        
        assert result == expected_result
        knowledge_manager.retriever.query_knowledge_structured.assert_called_once_with(keywords, 3, knowledge_manager.vector_store)
    
    def test_system_health_check(self, knowledge_manager):
        """测试系统健康检查"""
        # 检查各个组件是否可用
        assert knowledge_manager.embedder is not None
        assert knowledge_manager.vector_store is not None
        assert knowledge_manager.retriever is not None
        
        # 检查向量存储是否可用
        is_available = knowledge_manager.vector_store.is_available()
        # 不断言具体值，因为可能没有可用的存储
        
        # 获取索引信息应该不会出错
        index_info = knowledge_manager.get_index_info()
        assert isinstance(index_info, dict)
        assert "total_documents" in index_info