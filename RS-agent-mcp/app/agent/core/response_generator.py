"""
响应生成器 - 负责各种模式下的响应生成逻辑
"""

import logging
from typing import List, Optional, Dict, Any

from ...core.langchain_client import get_langchain_client
from ...services.billing.billing_tracker import get_billing_tracker
from .. import langchain_prompts
from ..tools.knowledge_tools import knowledge_tools

logger = logging.getLogger(__name__)

# 导入进度回报功能
try:
    from ...api.progress import report_progress, is_session_aborted
except ImportError:
    def report_progress(session_id, message, stage, metadata=None):
        pass
    def is_session_aborted(session_id):
        return False

class ResponseGenerator:
    """响应生成器"""
    
    def __init__(self):
        pass
    
    async def generate_knowledge_answer(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成知识问答答案
        
        Args:
            user_prompt: 用户输入
            file_paths: 文件路径列表
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            生成的答案
        """
        logger.info("开始生成知识答案...")
        
        try:
            # 1. 提取关键词
            if session_id:
                report_progress(session_id, "正在提取问题关键词...", "processing", 
                              {"step": "keyword_extraction"})
            
            keywords = await knowledge_tools.extract_keywords(user_prompt, file_paths, session_id, chat_history)
            logger.info(f"提取的关键词: {keywords}")
            
            # 检查是否被中止
            if session_id and is_session_aborted(session_id):
                return "任务已被用户中止"
            
            # 2. 知识检索
            if session_id:
                report_progress(session_id, "正在从知识库检索相关信息...", "processing", 
                              {"step": "knowledge_retrieval", "keywords_count": len(keywords)})
            
            context = await knowledge_tools.retrieve_knowledge(keywords)
            logger.info(f"检索到的知识: {context[:200] if context else '无内容'}...")
            
            # 检查是否被中止
            if session_id and is_session_aborted(session_id):
                return "任务已被用户中止"
            
            # 3. 检查检索结果
            if not context or context.strip() == "":
                return await self._generate_fallback_answer(user_prompt, file_paths, session_id, chat_history)
            
            # 4. 验证知识相关性
            if session_id:
                report_progress(session_id, "正在检查回答的准确性和相关性...", "processing", 
                              {"step": "knowledge_validation"})
            
            is_relevant = await knowledge_tools.validate_knowledge_relevance(user_prompt, context, session_id, chat_history)
            
            # 检查是否被中止
            if session_id and is_session_aborted(session_id):
                return "任务已被用户中止"
            
            if not is_relevant:
                return await self._generate_fallback_answer(user_prompt, file_paths, session_id, chat_history)
            
            # 5. 生成最终答案
            if session_id:
                report_progress(session_id, "正在生成专业回答...", "llm_call", 
                              {"step": "answer_generation", "model": "langchain"})
            
            return await self._generate_final_answer(user_prompt, context, file_paths, chat_history)
            
        except Exception as e:
            logger.error(f"知识问答出错: {str(e)}")
            return await self._generate_fallback_answer(user_prompt, file_paths, session_id, chat_history)
    
    async def generate_general_answer(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成通用答案
        
        Args:
            user_prompt: 用户输入
            file_paths: 文件路径列表
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            生成的答案
        """
        logger.info("开始生成通用答案...")
        
        try:
            if session_id:
                report_progress(session_id, "正在生成回答...", "llm_call", 
                              {"step": "general_answer", "model": "langchain"})
            
            file_info = self._get_file_info_string(file_paths)
            
            # 格式化会话历史
            formatted_history = ""
            if chat_history:
                formatted_history = langchain_prompts.format_chat_history(chat_history)
            
            # 选择合适的模板
            if chat_history:
                template = langchain_prompts.GENERAL_ANSWER_WITH_HISTORY_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info,
                    "chat_history": formatted_history
                }
            else:
                template = langchain_prompts.GENERAL_ANSWER_TEMPLATE
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
                formatted_prompt = template.format(**variables)
                human_msg = formatted_prompt
            
            response = await client.generate_response(human_msg, system_msg)
            
            # 记录LLM调用计费
            if session_id:
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "general_answer")
            
            return response
            
        except Exception as e:
            logger.error(f"通用回答出错: {str(e)}")
            return f"抱歉，处理您的请求时出现了问题: {str(e)}"
    
    async def _generate_final_answer(
        self,
        user_prompt: str,
        context: str,
        file_paths: Optional[List[str]] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成最终答案
        
        Args:
            user_prompt: 用户输入
            context: 检索到的知识上下文
            file_paths: 文件路径列表
            chat_history: 会话历史
            
        Returns:
            生成的最终答案
        """
        file_info = self._get_file_info_string(file_paths)
        
        # 格式化会话历史
        formatted_history = ""
        if chat_history:
            formatted_history = langchain_prompts.format_chat_history(chat_history)
        
        # 选择合适的模板
        if chat_history:
            template = langchain_prompts.FINAL_ANSWER_WITH_HISTORY_TEMPLATE
            variables = {
                "user_prompt": user_prompt,
                "file_info": file_info,
                "retrieved_content": context,
                "chat_history": formatted_history
            }
        else:
            template = langchain_prompts.FINAL_ANSWER_TEMPLATE
            variables = {
                "user_prompt": user_prompt,
                "file_info": file_info,
                "retrieved_content": context
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
            formatted_prompt = template.format(**variables)
            human_msg = formatted_prompt
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        session_id = getattr(self, '_current_session_id', None)
        if session_id:
            billing_tracker = get_billing_tracker()
            billing_tracker.track_llm_call(session_id, "langchain", "knowledge_answer")
        
        return response
    
    async def _generate_fallback_answer(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        生成回退答案
        
        Args:
            user_prompt: 用户输入
            file_paths: 文件路径列表
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            生成的回退答案
        """
        try:
            if session_id:
                report_progress(session_id, "知识库中无相关内容，使用通用知识回答...", "llm_call", 
                              {"step": "fallback_answer_generation", "model": "langchain"})
            
            file_info = self._get_file_info_string(file_paths)
            
            # 格式化会话历史
            formatted_history = ""
            if chat_history:
                formatted_history = langchain_prompts.format_chat_history(chat_history)
            
            # 选择合适的模板
            if chat_history:
                template = langchain_prompts.GENERAL_KNOWLEDGE_ANSWER_WITH_HISTORY_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info,
                    "chat_history": formatted_history
                }
            else:
                template = langchain_prompts.GENERAL_KNOWLEDGE_ANSWER_TEMPLATE
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
                human_msg = f"用户问题：{user_prompt}\n上传文件信息：{file_info}"
                system_msg = "你是一个知识渊博、友好的AI助手，能够回答各个领域的问题。请根据你的知识为用户提供准确、有帮助的回答。"
            
            fallback_answer = await client.generate_response(human_msg, system_msg)
            
            # 记录LLM调用计费
            if session_id:
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "fallback_answer_generation")
            
            # 在回答前添加免责声明
            final_answer = f"注意：以下回答不是基于我的专业知识库，而是基于通用知识的回答。\n\n{fallback_answer}"
            
            if session_id:
                report_progress(session_id, "已使用通用知识生成回答", "completed")
            
            return final_answer
            
        except Exception as e:
            logger.error(f"回退机制生成回答失败: {str(e)}")
            return f"抱歉，无法为您提供回答。错误：{str(e)}"
    
    def _get_file_info_string(self, file_paths: Optional[List[str]]) -> str:
        """获取文件信息字符串"""
        import os
        
        if not file_paths:
            return "无文件上传"
        
        file_info = []
        for path in file_paths:
            if os.path.exists(path):
                size = os.path.getsize(path)
                file_info.append(f"{os.path.basename(path)} ({size} bytes)")
            else:
                file_info.append(f"{os.path.basename(path)} (文件不存在)")
        
        return "，".join(file_info)

# 全局响应生成器实例
response_generator = ResponseGenerator()