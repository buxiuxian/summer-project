"""
线程安全的知识库管理器
解决多进程环境下的初始化竞争条件问题
"""

import os
import json
import time
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from contextlib import contextmanager

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class KnowledgeBaseStatus:
    """知识库状态信息"""
    is_ready: bool = False
    total_documents: int = 0
    embedding_dimension: int = 0
    load_time: float = 0.0
    last_accessed: float = 0.0
    error_count: int = 0

class ThreadSafeKnowledgeManager:
    """线程安全的知识库管理器"""
    
    _instance = None
    _lock = threading.Lock()
    _init_lock = threading.Lock()
    
    def __new__(cls):
        """单例模式确保全局只有一个实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.status = KnowledgeBaseStatus()
        self.knowledge_manager = None
        self._initialization_complete = False
        self._initialization_error = None
        
        # 启动初始化
        self._warm_up()
        self._initialized = True
    
    def _warm_up(self):
        """预热知识库，避免冷启动问题"""
        logger.info("🔥 开始知识库预热...")
        start_time = time.time()
        
        try:
            # 导入在这里进行，避免循环导入
            from app.rag.core.knowledge_manager import KnowledgeBaseManager
            
            # 创建知识库管理器
            self.knowledge_manager = KnowledgeBaseManager()
            
            # 检查索引状态
            index_info = self.knowledge_manager.get_index_info()
            
            self.status.total_documents = index_info.get('total_documents', 0)
            self.status.embedding_dimension = index_info.get('embedding_dimension', 0)
            self.status.is_ready = True
            self.status.load_time = time.time() - start_time
            
            logger.info(f"✅ 知识库预热完成，耗时 {self.status.load_time:.2f}s")
            logger.info(f"📊 索引状态: {self.status.total_documents} 个文档, "
                       f"维度 {self.status.embedding_dimension}")
            
            # 验证查询功能
            self._verify_query_functionality()
            
        except Exception as e:
            self.status.error_count += 1
            self._initialization_error = str(e)
            logger.error(f"❌ 知识库预热失败: {e}")
            # 不抛出异常，允许系统继续运行
    
    def _verify_query_functionality(self):
        """验证查询功能是否正常"""
        try:
            # 执行一个简单的查询测试
            test_keywords = [{'keyword': 'test', 'weight': 1.0}]
            result = self.knowledge_manager.query_knowledge(test_keywords, top_k=1)
            
            if len(result) > 0:
                logger.info("✅ 知识库查询功能验证通过")
            else:
                logger.warning("⚠️ 知识库查询功能可能异常")
                
        except Exception as e:
            logger.warning(f"⚠️ 知识库查询验证失败: {e}")
    
    @contextmanager
    def get_manager(self):
        """获取知识库管理器的上下文管理器"""
        if not self.status.is_ready:
            logger.warning("⚠️ 知识库尚未完全初始化，等待中...")
            # 等待最多5秒
            wait_start = time.time()
            while not self.status.is_ready and (time.time() - wait_start) < 5:
                time.sleep(0.1)
        
        self.status.last_accessed = time.time()
        
        if self.knowledge_manager is None:
            raise RuntimeError("知识库管理器未正确初始化")
        
        try:
            yield self.knowledge_manager
        except Exception as e:
            self.status.error_count += 1
            logger.error(f"知识库操作错误: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取知识库状态"""
        return {
            'is_ready': self.status.is_ready,
            'total_documents': self.status.total_documents,
            'embedding_dimension': self.status.embedding_dimension,
            'load_time': self.status.load_time,
            'last_accessed': self.status.last_accessed,
            'error_count': self.status.error_count,
            'initialization_error': self._initialization_error
        }
    
    def health_check(self) -> bool:
        """健康检查"""
        if not self.status.is_ready:
            return False
        
        try:
            with self.get_manager() as manager:
                # 执行健康检查查询
                test_keywords = [{'keyword': 'health', 'weight': 1.0}]
                result = manager.query_knowledge(test_keywords, top_k=1)
                return len(result) > 0
        except Exception:
            return False


# 全局实例
_thread_safe_manager = ThreadSafeKnowledgeManager()

def get_knowledge_manager():
    """获取线程安全的知识库管理器"""
    return _thread_safe_manager

def knowledge_health_check():
    """知识库健康检查"""
    return _thread_safe_manager.health_check()

def get_knowledge_status():
    """获取知识库状态"""
    return _thread_safe_manager.get_status()