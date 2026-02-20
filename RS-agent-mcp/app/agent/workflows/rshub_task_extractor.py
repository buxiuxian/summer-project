"""
RSHub任务提取组件 - 处理会话历史中的任务信息提取
"""

import json
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


class RSHubTaskExtractor:
    """RSHub任务提取器 - 从会话历史中智能提取任务信息"""
    
    @staticmethod
    async def extract_task_info_from_history(
        chat_history: Optional[List[Dict[str, Any]]], 
        user_prompt: str, 
        client: Any, 
        session_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        从会话历史中提取任务信息，使用LLM智能匹配用户想要的具体任务
        
        Args:
            chat_history: 会话历史
            user_prompt: 用户当前的提示词
            client: LangChain客户端
            session_id: 会话ID
        
        Returns:
            提取的任务信息字典，如果没有找到则返回None
        """
        if not chat_history:
            logger.warning("没有会话历史，无法提取任务信息")
            return None
        
        # 首先收集所有包含任务信息的历史消息
        task_messages = []
        for i, message in enumerate(chat_history):
            if message.get('role') == 'assistant':
                content = message.get('content', '')
                
                # 查找包含JSON格式任务详细信息的消息
                if '**任务详细信息**' in content and '```json' in content:
                    try:
                        # 提取JSON部分
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        if json_end == -1:
                            continue
                        
                        json_str = content[json_start:json_end].strip()
                        task_info = json.loads(json_str)
                        
                        # 验证必要的字段
                        required_fields = ['project_name', 'scenario_info', 'model_name', 'observation_modes', 'tasks', 'data_dicts']
                        if all(field in task_info for field in required_fields):
                            task_messages.append({
                                'index': i,
                                'task_info': task_info,
                                'content': content,
                                'project_name': task_info.get('project_name', ''),
                                'scenario': task_info.get('scenario_info', {}).get('name', ''),
                                'model': task_info.get('model_name', ''),
                                'timestamp': task_info.get('timestamp', '')
                            })
                            logger.info(f"找到任务 {len(task_messages)}: {task_info.get('project_name', '')} - {task_info.get('scenario_info', {}).get('name', '')}")
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"解析任务信息失败: {str(e)}")
                        continue
        
        if not task_messages:
            logger.warning("未找到任何有效的任务信息")
            return None
        
        logger.info(f"总共找到 {len(task_messages)} 个任务")
        
        # 如果只有一个任务，直接返回
        if len(task_messages) == 1:
            logger.info("只有一个任务，直接返回")
            return task_messages[0]['task_info']
        
        # 如果有多个任务，使用LLM来智能匹配
        try:
            return await RSHubTaskExtractor._llm_match_task(
                task_messages, user_prompt, client, session_id
            )
        except Exception as e:
            logger.error(f"使用LLM分析任务失败: {str(e)}")
            # 如果LLM分析失败，返回最近的任务作为备选
            logger.info("LLM分析失败，使用最近的任务作为备选")
            return task_messages[-1]['task_info']
    
    @staticmethod
    async def _llm_match_task(
        task_messages: List[Dict], 
        user_prompt: str, 
        client: Any, 
        session_id: Optional[str] = None
    ) -> Optional[Dict]:
        """使用LLM智能匹配任务"""
        try:
            from ..langchain_prompts import get_rshub_task_extraction_prompt, format_chat_history
            
            logger.info("开始使用LLM智能匹配任务")
            
            # 格式化会话历史
            formatted_history = format_chat_history(task_messages[0]['content'])  # 使用第一个任务的上下文
            
            # 创建任务概览信息，帮助LLM理解可选的任务
            task_overview = "可选的任务：\n"
            for i, task_msg in enumerate(task_messages):
                task_overview += f"{i+1}. 项目名称: {task_msg['project_name']}\n"
                task_overview += f"   场景类型: {task_msg['scenario']}\n"
                task_overview += f"   模型名称: {task_msg['model']}\n"
                task_overview += f"   时间戳: {task_msg['timestamp']}\n\n"
            
            logger.info(f"任务概览:\n{task_overview}")
            
            # 组合完整的会话历史和任务概览
            full_context = f"{formatted_history}\n\n{task_overview}"
            
            # 使用LLM分析用户想要的任务
            prompt = get_rshub_task_extraction_prompt(user_prompt, full_context)
            
            if session_id:
                try:
                    from ...api.progress import report_progress
                    report_progress(session_id, "正在使用AI智能匹配任务...", "processing")
                except ImportError:
                    pass
            
            logger.info(f"用户请求: {user_prompt}")
            logger.info("开始调用LLM进行任务匹配")
            
            # 调用LLM - 使用正确的LangChain客户端API
            variables = {
                "user_prompt": user_prompt,
                "chat_history": full_context
            }
            
            # 提取系统消息和用户消息
            system_msg = None
            human_msg = None
            
            try:
                # 获取格式化后的消息
                messages = prompt.format_messages(**variables)
                if len(messages) >= 2:
                    system_msg = messages[0].content if hasattr(messages[0], 'content') else None
                    human_msg = messages[1].content if hasattr(messages[1], 'content') else messages[1]
                elif len(messages) == 1:
                    human_msg = messages[0].content if hasattr(messages[0], 'content') else messages[0]
            except Exception as format_error:
                logger.error(f"格式化消息失败: {str(format_error)}")
                # 如果格式化失败，使用基本方式
                human_msg = f"用户当前请求：{user_prompt}\n\n会话历史和可选任务：\n{full_context}"
            
            response = await client.generate_response(human_msg, system_msg)
            
            # 解析LLM返回的项目名称
            response_text = response.strip() if isinstance(response, str) else str(response).strip()
            target_project_name = response_text.split('\n')[-1].strip()
            
            logger.info(f"LLM完整回复: {response_text}")
            logger.info(f"LLM分析结果: 目标项目名称 = {target_project_name}")
            
            if target_project_name == "NOT_FOUND":
                logger.warning("LLM未能识别用户想要的任务")
                return None
            
            # 根据LLM的分析结果找到对应的任务
            for task_msg in task_messages:
                if task_msg['project_name'] == target_project_name:
                    logger.info(f"成功精确匹配到任务: {target_project_name}")
                    return task_msg['task_info']
            
            # 如果没有精确匹配，尝试模糊匹配
            for task_msg in task_messages:
                if (target_project_name in task_msg['project_name'] or 
                    target_project_name in task_msg['scenario'] or 
                    target_project_name in task_msg['model']):
                    logger.info(f"模糊匹配到任务: {task_msg['project_name']}")
                    return task_msg['task_info']
            
            logger.warning(f"未能找到匹配的任务: {target_project_name}")
            # 如果LLM分析失败，返回最近的任务作为备选
            logger.info("使用最近的任务作为备选")
            return task_messages[-1]['task_info']
            
        except Exception as e:
            logger.error(f"LLM任务匹配失败: {str(e)}", exc_info=True)
            raise


class RSHubSubmissionHelper:
    """RSHub任务提交辅助器"""
    
    @staticmethod
    async def should_generate_log(user_prompt: str) -> bool:
        """判断是否需要生成日志"""
        # 简单判断：如果用户提到日志相关词汇
        log_keywords = ['日志', 'log', '记录', 'record']
        prompt_lower = user_prompt.lower()
        
        return any(keyword in prompt_lower for keyword in log_keywords)
    
    @staticmethod
    async def generate_log(project_name: str, tasks: List[Dict], data_dicts: List[Dict]) -> None:
        """生成日志文件"""
        try:
            import datetime
            now = datetime.datetime.now()
            log_content = []
            log_content.append(f"======{now.strftime('%Y%m%d%H%M%S')}======")
            log_content.append(f"project_name = {project_name}")
            
            for i, (task, data) in enumerate(zip(tasks, data_dicts)):
                log_content.append(f"task_name{i+1} = {task['name']}")
                log_content.append(f"data{i+1} = {data}")
            
            log_content.append("================================")
            
            # 写入日志文件
            with open("rshub_task_log.txt", "a", encoding="utf-8") as f:
                f.write("\n".join(log_content) + "\n")
            
            logger.info("日志已生成")
        except Exception as e:
            logger.error(f"生成日志失败: {str(e)}")
    
    @staticmethod
    def detect_param_count_and_create_tasks(exec_globals, scenario_info, model_name, observation_modes, timestamp, project_name, extracted_dicts=None):
        """检测参数字典数量并创建对应的任务列表"""
        # 先检测有多少个有效的参数字典
        param_count = 0
        
        # 方法1: 查找所有字典类型的变量
        dict_variables = []
        for var_name, var_value in exec_globals.items():
            if (isinstance(var_value, dict) and 
                not var_name.startswith('__') and 
                var_name not in ['np', 'datetime', 'copy']):
                # 检查是否包含RSHub相关的参数（包括土壤场景的theta_i_deg）
                if any(key in var_value for key in ['fGHz', 'scatters', 'sm', 'angle', 'depth', 'theta_i_deg', 'ks', 'kl']):
                    dict_variables.append((var_name, var_value))
        
        param_count = len(dict_variables)
        
        # 方法2: 如果有tasks变量（包含多个任务的结构），优先使用
        if 'tasks' in exec_globals and isinstance(exec_globals['tasks'], list):
            tasks_var = exec_globals['tasks']
            task_data_count = 0
            for task_item in tasks_var:
                if isinstance(task_item, dict):
                    if 'data' in task_item and isinstance(task_item['data'], dict):
                        task_data_count += 1
                    elif 'params' in task_item and isinstance(task_item['params'], dict):
                        task_data_count += 1
            
            if task_data_count > 0:
                param_count = task_data_count
        
        # 如果没有检测到多个参数，使用默认逻辑
        if param_count == 0:
            param_count = len(observation_modes)
        
        logger.info(f"检测到参数字典数量: {param_count}")
        
        # 创建对应数量的任务
        tasks = []
        
        if scenario_info['name'] == 'soil':  # 土壤场景特殊处理
            for i in range(param_count):
                # 土壤场景使用单任务计算所有角度
                if param_count == 1:
                    task_name = f"{scenario_info['name']}-{model_name}-{timestamp}"
                else:
                    task_name = f"{scenario_info['name']}-{model_name}-{i+1}-{timestamp}"
                
                tasks.append({
                    'name': task_name,
                    'output_var': 'bs'  # 土壤默认用bs标记
                })
        else:
            # 对于多参数情况，每个参数字典对应一个任务
            for i in range(param_count):
                # 基础任务名
                if param_count == 1:
                    # 单任务情况，使用观测模式名
                    mode = observation_modes[0] if observation_modes else 'passive'
                    task_name = f"{scenario_info['name']}-{model_name}-{mode}-{timestamp}"
                else:
                    # 多任务情况，使用序号区分
                    mode = observation_modes[0] if observation_modes else 'passive'
                    task_name = f"{scenario_info['name']}-{model_name}-{mode}-{i+1}-{timestamp}"
                
                output_var = 'bs' if (observation_modes and 'active' in observation_modes[0]) else 'tb'
                tasks.append({
                    'name': task_name,
                    'output_var': output_var
                })
        
        return tasks