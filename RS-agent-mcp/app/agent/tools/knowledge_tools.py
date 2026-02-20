"""
知识工具 - 负责知识库相关的工具函数
"""

import re
import logging
from typing import List, Optional, Dict, Any

from ...core.langchain_client import get_langchain_client
from ...services.billing.billing_tracker import get_billing_tracker
from .. import langchain_prompts
from ...rag import knowledge_base

logger = logging.getLogger(__name__)

# 导入进度回报功能
try:
    from ...api.progress import report_progress
except ImportError:
    def report_progress(session_id, message, stage, metadata=None):
        pass

class KnowledgeTools:
    """知识工具类"""
    
    def __init__(self):
        pass
    
    async def extract_keywords(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        使用LangChain从用户输入中提取关键词和权重
        
        Args:
            user_prompt: 用户输入
            file_paths: 文件路径列表
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            关键词和权重列表
        """
        try:
            if session_id:
                report_progress(session_id, "正在调用AI模型提取关键词...", "llm_call", 
                              {"model": "langchain", "task": "keyword_extraction"})
            
            file_info = self._get_file_info_string(file_paths)
            
            # 格式化会话历史
            formatted_history = ""
            if chat_history:
                formatted_history = langchain_prompts.format_chat_history(chat_history)
            
            # 选择合适的模板
            if chat_history:
                template = langchain_prompts.KEYWORD_EXTRACTION_WITH_HISTORY_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info,
                    "chat_history": formatted_history
                }
            else:
                template = langchain_prompts.KEYWORD_EXTRACTION_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info
                }
            
            # 使用LangChain客户端调用模板
            client = await get_langchain_client()
            
            # 提取系统消息和用户消息
            system_msg = None
            human_msg = None
            
            try:
                messages = template.format_messages(**variables)
                if len(messages) >= 2:
                    system_msg = messages[0].content if hasattr(messages[0], 'content') else None
                    human_msg = messages[1].content if hasattr(messages[1], 'content') else messages[1]
                elif len(messages) == 1:
                    human_msg = messages[0].content if hasattr(messages[0], 'content') else messages[0]
            except:
                human_msg = f"请根据用户的问题 \"{user_prompt}\"，提取相关的英文关键词。重要：提取的关键词必须是英文，即使用户问题是中文。"
                system_msg = "你是微波遥感领域的专家，擅长从用户问题中提取相关的技术关键词。无论用户问题是什么语言，提取的关键词必须使用英文，这样能更有效地检索英文文献。"
            
            response = await client.generate_response(human_msg, system_msg)
            
            # 记录LLM调用计费
            if session_id:
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "keyword_extraction")
            
            # 从响应中解析关键词
            keywords = self._parse_keywords_from_response(response)
            
            if not keywords:
                # 如果LangChain提取失败，使用简单备用方法
                logger.warning("LangChain关键词提取失败，使用备用方法")
                return self._extract_keywords_simple(user_prompt)
            
            return keywords
            
        except Exception as e:
            logger.error(f"LangChain关键词提取出错: {str(e)}")
            # 降级到简单关键词提取
            return self._extract_keywords_simple(user_prompt)
    
    async def retrieve_knowledge(
        self,
        keywords: List[Dict[str, Any]]
    ) -> str:
        """
        从知识库检索相关知识
        
        Args:
            keywords: 关键词和权重列表
            
        Returns:
            检索到的知识内容
        """
        try:
            if not keywords:
                return ""
            
            # 使用知识库管理器进行查询
            results = knowledge_base.query_domain_science_db_structured(keywords, top_k=5)
            
            if not results:
                return ""
            
            # 构建上下文文本
            context_parts = []
            for result in results:
                context_parts.append(f"=== 来源: {result['source']} (相似度: {result['similarity']:.3f}) ===\n{result['content']}")
            
            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"知识检索出错: {str(e)}")
            return ""
    
    async def validate_knowledge_relevance(
        self,
        user_prompt: str,
        retrieved_content: str,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        使用LangChain验证检索到的知识与用户问题的相关性
        
        Args:
            user_prompt: 用户输入
            retrieved_content: 检索到的内容
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            是否相关
        """
        try:
            if session_id:
                report_progress(session_id, "正在调用AI模型验证知识相关性...", "llm_call", 
                              {"model": "langchain", "task": "knowledge_validation"})
            
            # 格式化会话历史
            formatted_history = ""
            if chat_history:
                formatted_history = langchain_prompts.format_chat_history(chat_history)
            
            # 选择合适的模板
            if chat_history:
                template = langchain_prompts.KNOWLEDGE_VALIDATION_WITH_HISTORY_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "retrieved_content": retrieved_content,
                    "chat_history": formatted_history
                }
            else:
                template = langchain_prompts.KNOWLEDGE_VALIDATION_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "retrieved_content": retrieved_content
                }
            
            # 使用LangChain客户端调用模板
            client = await get_langchain_client()
            
            # 提取系统消息和用户消息
            system_msg = None
            human_msg = None
            
            try:
                messages = template.format_messages(**variables)
                if len(messages) >= 2:
                    system_msg = messages[0].content if hasattr(messages[0], 'content') else None
                    human_msg = messages[1].content if hasattr(messages[1], 'content') else messages[1]
                elif len(messages) == 1:
                    human_msg = messages[0].content if hasattr(messages[0], 'content') else messages[0]
            except:
                human_msg = f"用户问题：{user_prompt}\n从知识库检索到的内容：{retrieved_content}\n\n请使用宽松的标准判断：只要内容涉及用户问题的主要概念都认为是相关的。"
                system_msg = "你是微波遥感领域的专家，请判断检索到的知识库内容是否与用户问题相关。判断标准应该宽松：只要内容涉及用户问题的主要概念，即使是具体应用或专业细节，都应该认为是有用的。如果相关输出\"0\"，完全无关才输出\"-1\"。"
            
            response = await client.generate_response(human_msg, system_msg)
            
            # 记录LLM调用计费
            if session_id:
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "knowledge_validation")
            
            # 提取最后一行的数字
            lines = response.strip().split('\n')
            last_line = lines[-1].strip()
            
            # 寻找数字
            if '0' in last_line:
                return True
            elif '-1' in last_line:
                return False
            else:
                # 如果无法确定，默认认为相关
                logger.warning(f"无法解析验证结果: {last_line}")
                return True
                
        except Exception as e:
            logger.error(f"LangChain知识验证出错: {str(e)}")
            # 如果验证失败，默认认为相关
            return True
    
    def _parse_keywords_from_response(self, response: str) -> List[Dict[str, Any]]:
        """从LLM响应中解析关键词和权重"""
        try:
            # 查找包含方括号的行
            lines = response.strip().split('\n')
            bracket_line = None
            
            for line in lines:
                if '[' in line and ']' in line:
                    bracket_line = line
                    break
            
            if not bracket_line:
                return []
            
            # 提取方括号内容
            start = bracket_line.find('[')
            end = bracket_line.find(']') + 1
            list_str = bracket_line[start:end]
            
            # 使用正则表达式提取关键词和权重对
            pattern = r'\(\s*["\']?([^"\'(),]+)["\']?\s*,\s*([0-9.]+)\s*\)'
            matches = re.findall(pattern, list_str)
            
            keywords = []
            for keyword, weight in matches:
                try:
                    weight_float = float(weight)
                    if weight_float >= 0.1:  # 过滤低权重
                        keywords.append({
                            "keyword": keyword.strip(),
                            "weight": weight_float
                        })
                except ValueError:
                    continue
            
            # 确保权重总和为1
            if keywords:
                total_weight = sum(k["weight"] for k in keywords)
                if total_weight > 0:
                    for k in keywords:
                        k["weight"] = k["weight"] / total_weight
            
            return keywords
            
        except Exception as e:
            print(f"关键词解析失败: {str(e)}")
            return []
    
    def _extract_keywords_simple(self, user_prompt: str) -> List[Dict[str, Any]]:
        """简单的关键词提取（备用方法）"""
        # 如果输入为空，返回空列表
        if not user_prompt or not user_prompt.strip():
            return []
        
        # 中文关键词到英文关键词的映射
        chinese_to_english_mapping = {
            '微波': ('Microwave', 0.3),
            '遥感': ('Remote Sensing', 0.3),
            '散射': ('Scattering', 0.2),
            '土壤': ('Soil', 0.2),
            '湿度': ('Moisture', 0.15),
            '参数': ('Parameters', 0.15),
            '反演': ('Inversion', 0.15),
            '建模': ('Modeling', 0.15),
            '雷达': ('Radar', 0.2),
            '介电': ('Dielectric', 0.15),
            '后向散射': ('Backscattering', 0.2),
            '极化': ('Polarization', 0.15)
        }
        
        prompt_lower = user_prompt.lower()
        found_keywords = []
        
        for chinese_keyword, (english_keyword, weight) in chinese_to_english_mapping.items():
            if chinese_keyword in prompt_lower:
                found_keywords.append({
                    "keyword": english_keyword,
                    "weight": weight
                })
        
        # 如果没有找到任何关键词，使用默认的英文关键词
        if not found_keywords:
            found_keywords = [
                {"keyword": "Microwave Remote Sensing", "weight": 0.5},
                {"keyword": "Parameter Analysis", "weight": 0.5}
            ]
        
        # 归一化权重
        total_weight = sum(k["weight"] for k in found_keywords)
        if total_weight > 0:
            for k in found_keywords:
                k["weight"] = k["weight"] / total_weight
        
        return found_keywords
    
    def _get_file_info_string(self, file_paths: Optional[List[str]]) -> str:
        """获取文件信息字符串"""
        import os
        
        if not file_paths:
            return ""
        
        file_info = []
        for path in file_paths:
            if os.path.exists(path):
                size = os.path.getsize(path)
                file_info.append(f"{os.path.basename(path)} ({size} bytes)")
            else:
                file_info.append(f"{os.path.basename(path)} (文件不存在)")
        
        return "，".join(file_info)

# 全局知识工具实例
knowledge_tools = KnowledgeTools()