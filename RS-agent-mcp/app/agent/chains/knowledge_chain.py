"""
增强知识查询 - 返回带有文件源信息的结构化结果
"""

import logging
from typing import List, Optional, Dict, Any

from ...core.langchain_client import get_langchain_client
from ...services.billing.billing_tracker import get_billing_tracker
from ...services.file_storage import file_storage_manager
from .. import langchain_prompts
from ..tools.knowledge_tools import knowledge_tools

logger = logging.getLogger(__name__)

# 导入进度回报功能
try:
    from ...api.progress import report_progress
except ImportError:
    def report_progress(session_id, message, stage, metadata=None):
        pass

async def run_knowledge_query_with_sources_structured(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> dict:
    """
    增强的知识问答函数，返回带有文件源信息的结构化结果
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        session_id: 会话ID
        chat_history: 会话历史消息列表
    
    Returns:
        包含答案和源文件信息的字典
    """
    try:
        logger.info("开始增强知识问答（带源信息）...")
        
        # 1. 提取关键词和权重
        if session_id:
            report_progress(session_id, "正在提取问题关键词...", "processing", 
                          {"step": "keyword_extraction"})
        
        keywords = await knowledge_tools.extract_keywords(user_prompt, file_paths, session_id, chat_history)
        logger.info(f"提取的关键词: {keywords}")
        
        # 2. 调用RAG模块进行结构化检索
        if session_id:
            report_progress(session_id, "正在从知识库检索相关信息...", "processing", 
                          {"step": "knowledge_retrieval", "keywords_count": len(keywords)})
        
        # 使用结构化查询获取详细的检索结果
        from ...rag import knowledge_base
        structured_results = knowledge_base.query_domain_science_db_structured(keywords, top_k=5)
        
        if not structured_results:
            return {
                "answer": "抱歉，我的知识库中没有找到与您问题相关的信息。请尝试重新表述您的问题或提供更多上下文。",
                "sources": [],
                "status": "no_results"
            }
        
        # 3. 构建上下文文本和源文件信息
        context_parts = []
        source_files = []
        
        for result in structured_results:
            context_parts.append(f"=== 来源: {result['source']} (相似度: {result['similarity']:.3f}) ===\n{result['content']}")
            
            # 查找文件映射信息
            file_mapping_id = result.get('file_mapping_id')
            if file_mapping_id:
                file_info = file_storage_manager.get_file_info(file_mapping_id)
                if file_info:
                    # 优先使用文件映射中的原始文件名
                    original_filename = file_info.get("original_filename")
                    display_name = file_info.get("display_name") or original_filename
                    
                    source_files.append({
                        "file_mapping_id": file_mapping_id,
                        "original_filename": original_filename,
                        "display_name": display_name,
                        "file_extension": file_info.get("file_extension"),
                        "can_preview": file_info.get("file_extension", "").lower() == ".pdf",
                        "similarity": result['similarity']
                    })
                else:
                    # 如果映射ID存在但找不到文件信息，跳过这个结果
                    continue
            else:
                # 对于没有文件映射的源（如系统内置知识），添加占位信息
                source_files.append({
                    "file_mapping_id": None,
                    "original_filename": result['source'],
                    "display_name": result['source'][:40] + "..." if len(result['source']) > 40 else result['source'],
                    "file_extension": ".txt",
                    "can_preview": False,
                    "similarity": result['similarity']
                })
        
        context = "\n\n".join(context_parts)
        
        # 4. 验证知识相关性
        if session_id:
            report_progress(session_id, "正在检查回答的准确性和相关性...", "processing", 
                          {"step": "knowledge_validation"})
        
        is_relevant = await knowledge_tools.validate_knowledge_relevance(user_prompt, context, session_id, chat_history)
        
        if not is_relevant:
            return {
                "answer": "抱歉，检索到的信息与您的问题相关性较低。请尝试重新表述您的问题或提供更多上下文。",
                "sources": [],
                "status": "low_relevance"
            }
        
        # 5. 使用LangChain生成最终答案
        if session_id:
            report_progress(session_id, "正在生成专业回答...", "llm_call", 
                          {"step": "answer_generation", "model": "langchain"})
        
        # 生成最终答案
        final_answer = await _generate_structured_final_answer(user_prompt, context, file_paths, chat_history)
        
        # 去重源文件
        unique_sources = []
        seen_files = set()
        for source in source_files:
            file_key = source.get("file_mapping_id") or source.get("original_filename", "")
            if file_key not in seen_files:
                unique_sources.append(source)
                seen_files.add(file_key)
        
        # 按相似度排序
        unique_sources.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            "answer": final_answer,
            "sources": unique_sources,
            "status": "success",
            "keywords_used": [kw.get('keyword', '') for kw in keywords]
        }
        
    except Exception as e:
        logger.error(f"增强知识问答处理出错: {str(e)}")
        return {
            "answer": f"抱歉，处理您的知识查询时遇到了问题：{str(e)}",
            "sources": [],
            "status": "error"
        }

async def _generate_structured_final_answer(
    user_prompt: str,
    context: str,
    file_paths: Optional[List[str]] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    生成结构化查询的最终答案
    
    Args:
        user_prompt: 用户输入
        context: 检索到的知识上下文
        file_paths: 文件路径列表
        chat_history: 会话历史
        
    Returns:
        生成的最终答案
    """
    file_info = _get_file_info_string(file_paths)
    
    # 格式化会话历史
    formatted_history = ""
    if chat_history:
        formatted_history = langchain_prompts.format_chat_history(chat_history)
    
    # 根据是否有会话历史选择合适的模板
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
        # 尝试获取格式化后的消息
        messages = template.format_messages(**variables)
        if len(messages) >= 2:
            system_msg = messages[0].content if hasattr(messages[0], 'content') else None
            human_msg = messages[1].content if hasattr(messages[1], 'content') else messages[1]
        elif len(messages) == 1:
            human_msg = messages[0].content if hasattr(messages[0], 'content') else messages[0]
    except:
        # 如果出错，使用简单格式化
        human_msg = f"用户问题：{user_prompt}\n知识库检索内容：{context}"
        system_msg = "你是微波遥感领域的专家，请基于提供的知识库内容为用户提供准确、专业的回答。"
    
    final_answer = await client.generate_response(human_msg, system_msg)
    
    # 记录LLM调用计费
    session_id = getattr(_generate_structured_final_answer, '_current_session_id', None)
    if session_id:
        billing_tracker = get_billing_tracker()
        billing_tracker.track_llm_call(session_id, "langchain", "structured_knowledge_answer")
    
    return final_answer

def _get_file_info_string(file_paths: Optional[List[str]]) -> str:
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