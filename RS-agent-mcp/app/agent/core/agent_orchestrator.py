"""
Agent编排器 - 负责协调各个组件的工作
"""

import os
import logging
from typing import List, Optional, Dict, Any

from .task_classifier import task_classifier
from .response_generator import response_generator
from ..tools.knowledge_tools import knowledge_tools
from ...core.langchain_client import get_langchain_client

logger = logging.getLogger(__name__)

# 导入进度回报功能
try:
    from ...api.progress import report_progress, is_session_aborted, clear_abort_flag
except ImportError:
    def report_progress(session_id, message, stage, metadata=None):
        pass
    def is_session_aborted(session_id):
        return False
    def clear_abort_flag(session_id):
        pass

class AgentOrchestrator:
    """Agent编排器"""
    
    def __init__(self):
        self.task_classifier = task_classifier
        self.response_generator = response_generator
        self.knowledge_tools = knowledge_tools
    
    async def process_task(
        self,
        instruction_mode: int,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        处理任务的主要入口点
        
        Args:
            instruction_mode: 指令模式
            user_prompt: 用户输入
            file_paths: 文件路径列表
            output_path: 输出路径
            session_id: 会话ID
            rshub_token: RSHub令牌
            chat_history: 会话历史
            
        Returns:
            处理结果
        """
        logger.info(f"Agent编排器开始处理任务: mode={instruction_mode}")
        
        # 清除之前的中止标记
        if session_id:
            clear_abort_flag(session_id)
        
        try:
            if instruction_mode == 0:
                # 任务分类模式
                return await self._handle_task_classification(user_prompt, file_paths, session_id, chat_history)
            elif instruction_mode == 1:
                # 知识问答模式
                return await self._handle_knowledge_query(user_prompt, file_paths, session_id, chat_history)
            elif instruction_mode == 2:
                # RSHub任务提交模式
                return await self._handle_rshub_submission(user_prompt, file_paths, session_id, rshub_token)
            elif instruction_mode == 3:
                # RSHub结果获取模式
                return await self._handle_rshub_result_retrieval(user_prompt, file_paths, output_path, session_id, rshub_token, chat_history)
            elif instruction_mode == 100:
                # 文档转换模式
                return await self._handle_document_conversion(user_prompt, file_paths, output_path, session_id)
            elif instruction_mode == -1:
                # 通用回答模式
                return await self._handle_general_answer(user_prompt, file_paths, session_id, chat_history)
            else:
                logger.warning(f"不支持的模式: {instruction_mode}")
                return f"抱歉，暂不支持指令模式 {instruction_mode}"
        
        except Exception as e:
            logger.error(f"任务处理失败: {str(e)}", exc_info=True)
            return f"抱歉，处理您的请求时遇到了问题：{str(e)}"
    
    async def _handle_task_classification(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """处理任务分类 - 只返回分类结果，不执行具体任务"""
        # 进行任务分类
        classified_mode = await self.task_classifier.classify_task(user_prompt, file_paths, session_id, chat_history)
        
        logger.info(f"任务分类结果: {classified_mode}")
        
        # 直接返回分类结果，不执行具体任务
        # 具体任务执行由chat_router的第二阶段处理
        return classified_mode  # 直接返回整数类型
    
    async def _handle_knowledge_query(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """处理知识查询"""
        return await self.response_generator.generate_knowledge_answer(user_prompt, file_paths, session_id, chat_history)
    
    async def _handle_general_answer(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """处理通用回答"""
        return await self.response_generator.generate_general_answer(user_prompt, file_paths, session_id, chat_history)
    
    async def _handle_rshub_submission(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None
    ) -> str:
        """处理RSHub任务提交"""
        try:
            # 导入RSHub工作流模块
            from ..rshub_workflow import run_rshub_task_submission
            
            # 获取LangChain客户端
            client = await get_langchain_client()
            
            # 执行RSHub任务提交工作流
            result = await run_rshub_task_submission(
                user_prompt=user_prompt,
                file_paths=file_paths,
                session_id=session_id,
                client=client,
                rshub_token=rshub_token
            )
            
            return result
            
        except Exception as e:
            logger.error(f"提交RSHub建模任务功能出错: {str(e)}", exc_info=True)
            return f"抱歉，提交RSHub建模任务时遇到了问题：{str(e)}"
    
    async def _handle_rshub_result_retrieval(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        rshub_token: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """处理RSHub结果获取"""
        try:
            # 导入RSHub工作流模块
            from ..rshub_workflow import run_rshub_result_retrieval
            
            # 获取LangChain客户端
            client = await get_langchain_client()
            
            # 执行RSHub结果获取工作流
            result = await run_rshub_result_retrieval(
                user_prompt=user_prompt,
                file_paths=file_paths,
                output_path=output_path,
                session_id=session_id,
                client=client,
                rshub_token=rshub_token,
                chat_history=chat_history
            )
            
            return result
            
        except Exception as e:
            logger.error(f"获取RSHub任务结果功能出错: {str(e)}", exc_info=True)
            return f"抱歉，获取RSHub任务结果时遇到了问题：{str(e)}"
    
    async def _handle_document_conversion(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """处理文档转换"""
        try:
            # 检查是否提供了文件路径
            if not file_paths or len(file_paths) == 0:
                return "错误：未提供需要转换的文档文件"
            
            # 获取第一个文件路径
            file_path = file_paths[0]
            
            # 从文档中提取文本内容
            from ...utils.document_processor import extract_document_text, validate_extracted_text
            
            extracted_text = extract_document_text(file_path)
            
            if not extracted_text:
                return "错误：无法从文档中提取文本内容"
            
            if not validate_extracted_text(extracted_text):
                return "错误：提取的文档内容质量不佳或过短"
            
            # 使用LangChain模板进行文档转换
            from .. import langchain_prompts
            template = langchain_prompts.DOCUMENT_CONVERSION_TEMPLATE
            variables = {
                "extracted_text": extracted_text
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
                human_msg = f"请将以下文档内容转换为结构化的Markdown格式：\n\n{extracted_text}"
                system_msg = "你是一个专业的文档处理专家。请根据用户上传的文件内容，总结和概括其中内容，以清晰的结构和准确的语言写成一篇markdown格式的文字。"
            
            markdown_content = await client.generate_response(human_msg, system_msg)
            
            if not markdown_content or len(markdown_content.strip()) < 100:
                return "错误：LangChain转换失败或生成内容过短"
            
            # 如果指定了输出路径，将Markdown内容写入文件
            if output_path:
                output_file = os.path.join(output_path, f"converted_document.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                logger.info(f"Markdown文档已保存到: {output_file}")
            
            return markdown_content
            
        except Exception as e:
            logger.error(f"文档转换出错: {str(e)}")
            return f"抱歉，转换文档时遇到了问题：{str(e)}"

# 全局Agent编排器实例
agent_orchestrator = AgentOrchestrator()