"""
RAG核心模块 - 知识检索器
负责知识库的查询和结果格式化
"""

import logging
from typing import List, Dict, Any

from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """知识检索器"""
    
    def __init__(self):
        pass
    
    def query_knowledge(self, keywords: List[Dict[str, Any]], top_k: int = 3, vector_store: VectorStoreManager = None) -> str:
        """查询知识库并返回格式化文本"""
        if vector_store is None:
            logger.warning("向量存储不可用")
            return self._get_default_knowledge_content()
        
        try:
            # 构建查询文本
            query_text = self._build_query_text(keywords)
            
            if not query_text.strip():
                logger.warning("查询文本为空")
                return self._get_default_knowledge_content()
            
            # 查询向量存储
            results = vector_store.query(query_text, top_k)
            
            if not results:
                logger.warning("没有找到相关文档")
                return self._get_default_knowledge_content()
            
            # 构建返回内容
            context_parts = []
            for result in results:
                content = result.get('content', '')
                source = result.get('source', 'unknown')
                score = result.get('similarity', result.get('score', 0.0))
                
                context_parts.append(f"=== 来源: {source} (相似度: {score:.3f}) ===\n{content}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"查询知识库时出错: {str(e)}")
            return self._get_default_knowledge_content()
    
    def query_knowledge_structured(self, keywords: List[Dict[str, Any]], top_k: int = 3, vector_store: VectorStoreManager = None) -> List[Dict[str, Any]]:
        """查询知识库并返回结构化结果"""
        if vector_store is None:
            logger.warning("向量存储不可用")
            return []
        
        try:
            # 构建查询文本
            query_text = self._build_query_text(keywords)
            
            if not query_text.strip():
                logger.warning("查询文本为空")
                return []
            
            # 查询向量存储
            results = vector_store.query(query_text, top_k)
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_result = {
                    'content': result.get('content', ''),
                    'source': result.get('source', 'unknown'),
                    'similarity': float(result.get('similarity', result.get('score', 0.0)))
                }
                
                # 添加文件映射信息
                if 'file_mapping_id' in result and result['file_mapping_id']:
                    formatted_result['file_mapping_id'] = result['file_mapping_id']
                
                formatted_results.append(formatted_result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"查询知识库时出错: {str(e)}")
            return []
    
    def _build_query_text(self, keywords: List[Dict[str, Any]]) -> str:
        """构建查询文本"""
        query_parts = []
        
        for item in keywords:
            keyword = item.get('keyword', '')
            weight = item.get('weight', 1.0)
            
            if not keyword.strip():
                continue
            
            # 根据权重重复关键词
            repeat_count = max(1, int(weight * 3))
            query_parts.extend([keyword] * repeat_count)
        
        return " ".join(query_parts)
    
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
    
    def extract_keywords_from_text(self, text: str, max_keywords: int = 10) -> List[str]:
        """从文本中提取关键词"""
        try:
            # 简单的关键词提取：去除停用词，选择高频词
            import re
            
            # 清理文本
            text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)  # 保留中英文、数字、空格
            
            # 简单的中文分词（按字符分割，实际应用中可以使用更专业的分词库）
            words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
            
            # 过滤停用词
            stop_words = {
                '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has'
            }
            
            # 统计词频
            word_freq = {}
            for word in words:
                if len(word) > 1 and word.lower() not in stop_words:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # 按词频排序，返回前N个
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
            
        except Exception as e:
            logger.error(f"提取关键词时出错: {str(e)}")
            return []
    
    def expand_query_with_synonyms(self, keywords: List[str], expansion_factor: int = 2) -> List[str]:
        """使用同义词扩展查询"""
        try:
            # 简单的同义词扩展（实际应用中可以使用专业的同义词库）
            synonym_dict = {
                '土壤': ['地面', '地表', '土地'],
                '湿度': ['水分', '含水量', '湿度'],
                '微波': ['电磁波', '遥感'],
                '散射': ['反射', '回波'],
                '植被': ['植物', '作物'],
                'snow': ['雪地', '雪层'],
                'soil': ['土壤', '地面'],
                'vegetation': ['植被', '植物']
            }
            
            expanded_keywords = keywords.copy()
            
            for keyword in keywords:
                # 查找同义词
                for key, synonyms in synonym_dict.items():
                    if key in keyword.lower():
                        expanded_keywords.extend(synonyms[:expansion_factor])
                        break
            
            return expanded_keywords
            
        except Exception as e:
            logger.error(f"扩展查询时出错: {str(e)}")
            return keywords
    
    def rank_results_by_relevance(self, results: List[Dict[str, Any]], query_keywords: List[str]) -> List[Dict[str, Any]]:
        """根据关键词相关性对结果重新排序"""
        try:
            if not results or not query_keywords:
                return results
            
            # 计算每个结果的相关性得分
            ranked_results = []
            for result in results:
                content = result.get('content', '').lower()
                source = result.get('source', '').lower()
                
                # 计算关键词匹配得分
                relevance_score = 0
                for keyword in query_keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in content:
                        relevance_score += content.count(keyword_lower) * 2
                    if keyword_lower in source:
                        relevance_score += 1
                
                # 添加原始相似度得分
                original_score = result.get('similarity', result.get('score', 0.0))
                combined_score = relevance_score * 0.3 + original_score * 0.7
                
                result['relevance_score'] = combined_score
                ranked_results.append(result)
            
            # 按相关性得分排序
            ranked_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"重新排序结果时出错: {str(e)}")
            return results