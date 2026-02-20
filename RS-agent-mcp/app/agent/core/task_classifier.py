"""
任务分类器 - 负责用户意图识别和任务类型分类
"""

import re
import logging
from typing import List, Optional, Dict, Any

from ...core.langchain_client import get_langchain_client
from ...services.billing.billing_tracker import get_billing_tracker
from .. import langchain_prompts

logger = logging.getLogger(__name__)

# 导入进度回报功能
try:
    from ...api.progress import report_progress, is_session_aborted
except ImportError:
    def report_progress(session_id, message, stage, metadata=None):
        pass
    def is_session_aborted(session_id):
        return False

class TaskClassifier:
    """任务分类器"""
    
    def __init__(self):
        self.supported_modes = [1, 2, 3, -1]  # 支持的任务类型
        
    async def classify_task(
        self,
        user_prompt: str,
        file_paths: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None
    ) -> int:
        """
        使用LangChain进行任务分类
        
        Args:
            user_prompt: 用户输入
            file_paths: 文件路径列表
            session_id: 会话ID
            chat_history: 会话历史
            
        Returns:
            任务类型编号
        """
        logger.info("开始任务分类...")
        
        # 进度回报
        if session_id:
            report_progress(session_id, "正在调用AI模型分析问题类型...", "llm_call", 
                          {"model": "langchain", "task": "task_classification"})
        
        try:
            # 检查是否被中止
            if session_id and is_session_aborted(session_id):
                return -100  # 用户主动中止请求
            
            # 获取文件信息
            file_info = self._get_file_info_string(file_paths)
            
            # 格式化会话历史
            formatted_history = ""
            if chat_history:
                formatted_history = langchain_prompts.format_chat_history(chat_history)
            
            # 选择合适的模板
            if chat_history:
                template = langchain_prompts.TASK_CLASSIFICATION_WITH_HISTORY_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info,
                    "chat_history": formatted_history
                }
            else:
                template = langchain_prompts.TASK_CLASSIFICATION_TEMPLATE
                variables = {
                    "user_prompt": user_prompt,
                    "file_info": file_info
                }
            
            # 使用LangChain客户端调用模板
            client = await get_langchain_client()
            formatted_prompt = template.format(**variables)
            
            # 提取系统消息和用户消息
            system_msg = None
            human_msg = formatted_prompt
            
            try:
                # 尝试获取格式化后的消息
                messages = template.format_messages(**variables)
                if len(messages) >= 2:
                    system_msg = messages[0].content if hasattr(messages[0], 'content') else None
                    human_msg = messages[1].content if hasattr(messages[1], 'content') else messages[1]
                elif len(messages) == 1:
                    human_msg = messages[0].content if hasattr(messages[0], 'content') else messages[0]
            except:
                # 如果出错，使用原始格式化方式
                pass
            
            response = await client.generate_response(human_msg, system_msg)
            
            # 记录LLM调用计费
            if session_id:
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "task_classification")
            
            # 从响应中提取任务类型
            task_type = self._extract_task_type_from_response(response)
            logger.info(f"任务分类结果: {task_type}")
            return task_type
            
        except Exception as e:
            logger.error(f"任务分类出错: {str(e)}")
            # 检查是否是超时或其他LLM调用错误
            error_str = str(e).lower()
            if 'timeout' in error_str or 'time out' in error_str:
                return -101  # LLM调用超时
            elif 'connection' in error_str or 'network' in error_str:
                return -102  # 网络连接错误
            elif 'accountoverdue' in error_str or '403' in error_str or 'forbidden' in error_str:
                return -103  # API认证或余额问题
            else:
                # 其他错误，降级到基于关键词的简单分类
                return self._classify_by_keywords(user_prompt)
    
    def _extract_task_type_from_response(self, response: str) -> int:
        """从LLM响应中提取任务类型编号"""
        try:
            # 验证响应格式，拒绝处理明显的错误信息
            response_lower = response.lower()
            
            # 检查是否是错误信息 - 使用更严格的检测
            error_patterns = [
                r'error code:\s*\d+',  # Error code: XXX
                r'^\d{3}\s*error',     # 404 error 开头
                r'抱歉，对话完成时出现问题',  # 特定错误前缀
                r'api\s*error',         # API error
                r'accountoverdue',      # 账户余额问题
                r'request\s*failed',     # 请求失败
                r'unauthorized',        # 未授权
                r'forbidden',           # 禁止访问
                r'rate\s*limit'          # 速率限制
            ]
            
            # 只有在明确匹配错误模式时才拒绝处理
            import re
            for pattern in error_patterns:
                if re.search(pattern, response_lower):
                    logger.warning(f"检测到错误信息模式，拒绝处理: {response[:100]}...")
                    return -1  # 返回通用回答，让系统降级处理
            
            # 检查孤立的错误代码（避免误判关于错误代码的讨论）
            isolated_error_codes = ['403', '500']
            for code in isolated_error_codes:
                # 只有当代码单独出现且在错误上下文中时才认为是错误
                if code in response_lower and any(word in response_lower for word in ['error', 'failed', 'forbidden', 'unauthorized']):
                    logger.warning(f"检测到错误代码，拒绝处理: {response[:100]}...")
                    return -1
            
            # === 改进的数字提取逻辑 ===
            # 方法1：从最后一行开始向前查找包含数字的行
            lines = response.strip().split('\n')
            task_type = None
            
            # 从最后一行开始向前查找，跳过空行
            for line in reversed(lines):
                line = line.strip()
                if not line:  # 跳过空行
                    continue
                    
                # 尝试从当前行提取数字
                numbers = re.findall(r'-?\d+', line)
                if numbers:
                    candidate = int(numbers[-1])  # 取最后一个数字
                    if candidate in self.supported_modes:
                        task_type = candidate
                        logger.info(f"从行 '{line}' 提取到任务类型: {task_type}")
                        break
            
            # 方法2：如果没找到，在整个响应中查找最后一个有效数字
            if task_type is None:
                all_numbers = re.findall(r'-?\d+', response)
                if all_numbers:
                    for num in reversed(all_numbers):
                        candidate = int(num)
                        if candidate in self.supported_modes:
                            task_type = candidate
                            logger.info(f"从整个响应中提取到任务类型: {task_type}")
                            break
            
            # 如果找到了有效数字，直接返回
            if task_type is not None:
                return task_type
            
            # === 数字提取失败，使用关键词匹配 ===
            # 知识问答关键词（最高优先级）
            knowledge_keywords = ['知识', '什么是', '什么', '如何', '为什么', '原理', '解释', '定义', '介绍', '说明']
            if any(keyword in response_lower for keyword in knowledge_keywords):
                return 1
            
            # RSHub建模任务关键词
            modeling_keywords = ['构建', '生成', '创建', '建模', '提交', '计算', '参数']
            if any(keyword in response_lower for keyword in modeling_keywords):
                return 2
            
            # RSHub结果获取关键词（需要更严格的匹配）
            result_keywords = ['获取', '结果', '可视化', '完成', '分析']
            # 只有当明确提到获取结果或之前任务时才返回3
            if any(keyword in response_lower for keyword in result_keywords):
                # 进一步检查是否真的在询问之前任务的结果
                context_keywords = ['刚才', '之前', '历史', '任务', '之前提交', '之前创建', '运行']
                if any(context in response_lower for context in context_keywords):
                    return 3
            
            # 默认返回知识问答
            return 1
                
        except Exception as e:
            logger.error(f"任务类型提取失败: {str(e)}")
            return -1
    
    def _classify_by_keywords(self, user_prompt: str) -> int:
        """基于关键词的简单任务分类（备用方法）"""
        prompt_lower = user_prompt.lower()
        
        # 知识问答关键词（最高优先级）
        knowledge_keywords = ['什么是', '什么', '如何', '为什么', '解释', '定义', '原理', '机制', '介绍', '说明']
        if any(keyword in prompt_lower for keyword in knowledge_keywords):
            return 1
        
        # RSHub建模任务关键词
        modeling_keywords = ['构建', '生成', '创建', '建立', '建模', '提交', '计算', '参数']
        if any(keyword in prompt_lower for keyword in modeling_keywords):
            return 2
        
        # RSHub结果获取关键词（需要更严格的匹配）
        result_keywords = ['获取', '结果', '可视化', '完成', '分析']
        if any(keyword in prompt_lower for keyword in result_keywords):
            # 只有当明确提到获取之前任务的结果时才返回3
            context_keywords = ['刚才', '之前', '历史', '任务', '之前提交', '之前创建', '运行']
            if any(context in prompt_lower for context in context_keywords):
                return 3
        
        # 默认返回知识问答
        return 1
    
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

# 全局任务分类器实例
task_classifier = TaskClassifier()