"""
Agent执行链模块
"""

from .knowledge_chain import run_knowledge_query_with_sources_structured

# 保留原有的链导入（如果存在）
try:
    from .knowledge_chain import KnowledgeChain
    from .classification_chain import ClassificationChain
    from .general_chain import GeneralChain
    __all__ = [
        "run_knowledge_query_with_sources_structured",
        "KnowledgeChain",
        "ClassificationChain", 
        "GeneralChain"
    ]
except ImportError:
    __all__ = [
        "run_knowledge_query_with_sources_structured"
    ]