"""
RSHub工作流可复用组件 - 提取自原始rshub_workflow.py的通用功能
"""

import os
import re
import json
import io
import logging
import datetime
import subprocess
import sys
from typing import List, Optional, Dict, Any, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

logger = logging.getLogger(__name__)

# 场景类型定义
SCENARIO_TYPES = {
    0: {'name': 'snow', 'name_cn': '雪地', 'models': ['qms', 'bic']},
    1: {'name': 'soil', 'name_cn': '土壤', 'models': ['aiem']},
    2: {'name': 'veg', 'name_cn': '植被', 'models': ['rt']}
}

# 模型名称映射
MODEL_NAMES = {
    'qms': 'DMRT-QMS',
    'bic': 'DMRT-BIC',
    'aiem': 'AIEM',
    'rt': 'VPRT'
}


class RSHubEnvironmentManager:
    """RSHub环境管理器"""
    
    @staticmethod
    async def check_and_install_rshub(session_id: Optional[str] = None) -> bool:
        """检查并安装rshub包"""
        try:
            import rshub
            return True
        except ImportError:
            logger.info("RSHub包未安装，正在安装...")
            if session_id:
                try:
                    from ...api.progress import report_progress
                    report_progress(session_id, "正在安装RSHub包...", "processing", 
                                  {"action": "pip_install"})
                except ImportError:
                    pass
            
            try:
                # 使用subprocess运行pip install
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "rshub"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    logger.info("RSHub包安装成功")
                    return True
                else:
                    logger.error(f"RSHub包安装失败: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"安装RSHub包时出错: {str(e)}")
                return False


class RSHubTaskAnalyzer:
    """RSHub任务分析器"""
    
    @staticmethod
    async def classify_scenario(user_prompt: str, file_paths: Optional[List[str]], 
                             client: Any, session_id: Optional[str] = None) -> int:
        """使用LLM判断场景类型"""
        from .. import langchain_prompts
        
        file_info = RSHubTaskAnalyzer._get_file_info_string(file_paths)
        
        template = langchain_prompts.RSHUB_SCENARIO_CLASSIFICATION_TEMPLATE
        variables = {
            "user_prompt": user_prompt,
            "file_info": file_info
        }
        
        # 格式化消息
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        if session_id:
            try:
                from ...services.billing.billing_tracker import get_billing_tracker
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "scenario_classification")
            except ImportError:
                pass
        
        # 提取场景类型
        try:
            lines = response.strip().split('\n')
            last_line = lines[-1].strip()
            
            numbers = re.findall(r'-?\d+', last_line)
            if numbers:
                scenario = int(numbers[-1])
                if scenario in [0, 1, 2]:
                    return scenario
        except:
            pass
        
        return -1
    
    @staticmethod
    async def select_model(scenario_type: int, user_prompt: str, 
                         client: Any, session_id: Optional[str] = None) -> str:
        """根据场景和用户需求选择模型"""
        from .. import langchain_prompts
        
        # 土壤和植被场景只有一个模型
        if scenario_type == 1:
            return 'aiem'
        elif scenario_type == 2:
            return 'rt'
        
        # 雪地场景需要判断
        template = langchain_prompts.RSHUB_MODEL_SELECTION_TEMPLATE
        variables = {
            "scenario_type": SCENARIO_TYPES[scenario_type]['name'],
            "user_prompt": user_prompt
        }
        
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        if session_id:
            try:
                from ...services.billing.billing_tracker import get_billing_tracker
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "model_selection")
            except ImportError:
                pass
        
        # 提取模型名称
        response_lower = response.lower()
        if 'bic' in response_lower:
            return 'bic'
        else:
            return 'qms'  # 默认
    
    @staticmethod
    async def determine_observation_modes(scenario_name: str, user_prompt: str,
                                       client: Any, session_id: Optional[str] = None) -> List[str]:
        """判断需要的观测模式"""
        from .. import langchain_prompts
        
        # 土壤场景特殊处理
        if scenario_name == 'soil':
            return ['active_passive']  # 土壤场景合并处理
        
        template = langchain_prompts.RSHUB_OBSERVATION_MODE_TEMPLATE
        variables = {
            "scenario_name": scenario_name,
            "user_prompt": user_prompt
        }
        
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        if session_id:
            try:
                from ...services.billing.billing_tracker import get_billing_tracker
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "observation_mode_determination")
            except ImportError:
                pass
        
        # 解析观测模式
        try:
            # 查找包含列表的行
            lines = response.strip().split('\n')
            for line in reversed(lines):
                if '[' in line and ']' in line:
                    # 提取列表内容
                    start = line.find('[')
                    end = line.find(']') + 1
                    list_str = line[start:end]
                    
                    # 解析列表
                    modes = eval(list_str)
                    if isinstance(modes, list):
                        return modes
        except:
            pass
        
        # 默认值
        if scenario_name == 'veg':
            return ['passive']
        else:
            return ['passive']  # 雪地默认passive
    
    @staticmethod
    def _get_file_info_string(file_paths: Optional[List[str]]) -> str:
        """获取文件信息字符串"""
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


class RSHubParameterManager:
    """RSHub参数管理器"""
    
    @staticmethod
    async def load_technical_docs(scenario_name: str) -> str:
        """加载场景相关的技术文档"""
        tech_doc_path = f"workflow_knowledge/{scenario_name}_parameters.md"
        
        if os.path.exists(tech_doc_path):
            with open(tech_doc_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 同时加载通用的RSHub技术文档（如果存在）
            general_doc_path = "workflow_knowledge/RSHub-Technical-documentation.md"
            if os.path.exists(general_doc_path):
                with open(general_doc_path, 'r', encoding='utf-8') as f:
                    general_content = f.read()
                    # 只提取相关场景的部分
                    if scenario_name == 'snow':
                        # 提取Snow Scenario部分
                        start = general_content.find("### Snow Scenario")
                        end = general_content.find("### Soil Scenario", start)
                    elif scenario_name == 'soil':
                        # 提取Soil Scenario部分
                        start = general_content.find("### Soil Scenario")
                        end = general_content.find("## Model Output Parameters", start)
                    elif scenario_name == 'veg':
                        # 提取Vegetation Scenario部分
                        start = general_content.find("### Vegetation Scenario")
                        end = general_content.find("### Snow Scenario", start)
                    else:
                        start = -1
                        end = -1
                    
                    if start > 0 and end > 0:
                        scenario_section = general_content[start:end]
                        content += f"\n\n--- 通用技术文档摘录 ---\n{scenario_section}"
            
            return content
        else:
            # 返回默认的技术文档摘要
            return f"场景：{scenario_name}\n请参考RSHub技术文档中的参数说明。"
    
    @staticmethod
    async def read_user_files(file_paths: Optional[List[str]]) -> str:
        """读取用户上传的文件内容"""
        if not file_paths:
            return "无上传文件"
        
        contents = []
        for path in file_paths:
            try:
                # 尝试提取文档内容
                from ...utils.document_processor import extract_document_text
                content = extract_document_text(path)
                if content:
                    contents.append(f"=== 文件：{os.path.basename(path)} ===\n{content}")
                else:
                    # 如果是文本文件，直接读取
                    if path.endswith(('.txt', '.csv', '.md')):
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            contents.append(f"=== 文件：{os.path.basename(path)} ===\n{content}")
            except Exception as e:
                logger.error(f"读取文件失败 {path}: {str(e)}")
        
        return "\n\n".join(contents) if contents else "无法读取文件内容"
    
    @staticmethod
    async def generate_parameter_code(scenario_info: Dict, model_name: str, 
                                   observation_modes: List[str], user_prompt: str,
                                   file_content: str, technical_docs: str,
                                   client: Any, session_id: Optional[str] = None) -> str:
        """生成参数填充代码"""
        from .. import langchain_prompts
        
        template = langchain_prompts.RSHUB_PARAMETER_PARSING_TEMPLATE
        variables = {
            "scenario_name": scenario_info['name'],
            "model_name": MODEL_NAMES.get(model_name, model_name),
            "observation_modes": ", ".join(observation_modes),
            "user_prompt": user_prompt,
            "file_content": file_content,
            "technical_docs": technical_docs
        }
        
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        if session_id:
            try:
                from ...services.billing.billing_tracker import get_billing_tracker
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "parameter_code_generation")
            except ImportError:
                pass
        
        # 提取代码块
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return ""
    
    @staticmethod
    async def fix_parameter_code(error_message: str, original_code: str, 
                              scenario_type: str, client: Any, 
                              session_id: Optional[str] = None) -> str:
        """使用LLM修复参数代码"""
        from .. import langchain_prompts
        
        template = langchain_prompts.RSHUB_ERROR_ANALYSIS_TEMPLATE
        variables = {
            "error_message": error_message,
            "original_code": original_code,
            "scenario_type": scenario_type
        }
        
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        if session_id:
            try:
                from ...services.billing.billing_tracker import get_billing_tracker
                billing_tracker = get_billing_tracker()
                billing_tracker.track_llm_call(session_id, "langchain", "parameter_code_fix")
            except ImportError:
                pass
        
        # 提取修复后的代码
        code_match = re.search(r'```python\n(.*?)\n```', response, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        return ""
    
    @staticmethod
    def extract_data_dicts_from_globals(exec_globals, num_tasks):
        """从执行全局变量中智能提取数据字典"""
        extracted_dicts = []
        
        def flatten_nested_params(data_dict):
            """展平嵌套的参数结构"""
            logger.info(f"尝试展平参数字典，原始键: {list(data_dict.keys())}")
            flattened = data_dict.copy()
            
            # 检查多种可能的嵌套键名
            nested_keys = ['params', 'parameters', 'param']
            
            for key in nested_keys:
                if key in data_dict and isinstance(data_dict[key], dict):
                    # 如果有嵌套的参数字典，将其内容提升到顶级
                    nested_params = flattened.pop(key)
                    logger.info(f"发现嵌套结构: {key} -> {list(nested_params.keys())}")
                    flattened.update(nested_params)
                    logger.info(f"展平后的键: {list(flattened.keys())}")
                    logger.info(f"展平嵌套参数结构，原结构有{key}子字典，包含{len(nested_params)}个参数")
                    return flattened
            
            logger.info("未发现嵌套结构，返回原始字典")
            return data_dict
        
        # 方法1: 尝试标准的data、data1、data2...变量名
        for i in range(num_tasks):
            data_key = f'data{i+1}' if num_tasks > 1 and i > 0 else 'data'
            if data_key in exec_globals and isinstance(exec_globals[data_key], dict):
                var_value = exec_globals[data_key]
                
                # 检查是否包含RSHub相关的参数（直接或嵌套）
                has_direct_params = any(key in var_value for key in ['fGHz', 'scatters', 'sm', 'angle', 'depth', 'theta_i_deg', 'ks', 'kl'])
                has_meta_keys = any(key in var_value for key in ['model', 'scenario'])
                
                # 检查嵌套结构
                has_nested_params = False
                nested_keys = ['params', 'parameters', 'param']
                for nested_key in nested_keys:
                    if (nested_key in var_value and 
                        isinstance(var_value[nested_key], dict) and
                        any(key in var_value[nested_key] for key in ['fGHz', 'scatters', 'sm', 'angle', 'depth', 'theta_i_deg', 'ks', 'kl'])):
                        has_nested_params = True
                        break
                
                if has_direct_params or has_meta_keys or has_nested_params:
                    logger.info(f"方法1: 找到数据变量 {data_key}")
                    data_dict = flatten_nested_params(var_value.copy())
                    extracted_dicts.append(data_dict)
        
        # 如果方法1成功找到足够的字典，返回结果
        if len(extracted_dicts) == num_tasks:
            return extracted_dicts
        
        # 方法2: 查找所有字典类型的变量，按名称排序
        dict_variables = []
        for var_name, var_value in exec_globals.items():
            if (isinstance(var_value, dict) and 
                not var_name.startswith('__') and 
                var_name not in ['np', 'datetime', 'copy']):
                
                # 检查是否直接包含RSHub相关的参数
                has_direct_params = any(key in var_value for key in ['fGHz', 'scatters', 'sm', 'angle', 'depth', 'theta_i_deg', 'ks', 'kl'])
                
                # 检查是否有嵌套的参数结构（支持多种键名）
                has_nested_params = False
                nested_keys = ['params', 'parameters', 'param']
                
                for nested_key in nested_keys:
                    if (nested_key in var_value and 
                        isinstance(var_value[nested_key], dict) and
                        any(key in var_value[nested_key] for key in ['fGHz', 'scatters', 'sm', 'angle', 'depth', 'theta_i_deg', 'ks', 'kl'])):
                        has_nested_params = True
                        break
                
                if has_direct_params or has_nested_params:
                    flattened_dict = flatten_nested_params(var_value.copy())
                    dict_variables.append((var_name, flattened_dict))
        
        # 按变量名排序（确保一致的顺序）
        dict_variables.sort(key=lambda x: x[0])
        
        # 取前num_tasks个字典
        if len(dict_variables) >= num_tasks:
            return [var_value for _, var_value in dict_variables[:num_tasks]]
        
        # 方法3: 如果有tasks变量（包含多个任务的结构），尝试提取
        if 'tasks' in exec_globals and isinstance(exec_globals['tasks'], list):
            tasks_var = exec_globals['tasks']
            extracted_from_tasks = []
            for task_item in tasks_var:
                if isinstance(task_item, dict):
                    if 'data' in task_item and isinstance(task_item['data'], dict):
                        flattened_data = flatten_nested_params(task_item['data'].copy())
                        extracted_from_tasks.append(flattened_data)
                    elif 'params' in task_item and isinstance(task_item['params'], dict):
                        extracted_from_tasks.append(task_item['params'].copy())
            
            if len(extracted_from_tasks) >= num_tasks:
                return extracted_from_tasks[:num_tasks]
        
        return []


class RSHubTaskManager:
    """RSHub任务管理器"""
    
    @staticmethod
    async def wait_for_tasks(token: str, project_name: str, tasks: List[Dict], 
                           session_id: Optional[str] = None) -> Tuple[bool, str]:
        """等待所有任务完成"""
        from rshub import submit_jobs
        
        start_time = datetime.datetime.now()
        check_interval = 10  # 固定每10秒检查一次
        timeout_seconds = 120  # 轮询超时时间为120秒
        
        while True:
            # 检查是否被中止
            if session_id:
                try:
                    from ...api.progress import is_session_aborted
                    if is_session_aborted(session_id):
                        logger.info("任务被用户中止")
                        return (False, "用户中止")
                except ImportError:
                    pass
            
            # 检查所有任务状态
            all_completed = True
            failed_task = None
            
            for task in tasks:
                try:
                    result = submit_jobs.check_completion(token, project_name, task['name'])
                    result_str = str(result)
                    
                    # 检查任务是否失败
                    if "Jobs are failed" in result_str:
                        logger.error(f"任务失败: {task['name']} - {result_str}")
                        failed_task = task['name']
                        return (False, f"RSHub服务器任务失败: {failed_task}")
                    
                    # 检查任务是否完成
                    if "Jobs are completed" not in result_str:
                        all_completed = False
                        break
                        
                except Exception as e:
                    logger.error(f"检查任务状态失败: {str(e)}")
                    all_completed = False
                    break
            
            if all_completed:
                return (True, "")
            
            # 计算等待时间
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            
            # 120秒超时检查
            if elapsed > timeout_seconds:
                logger.warning(f"任务轮询超时: 已等待{timeout_seconds}秒，任务仍在执行中")
                timeout_message = (
                    f"任务轮询已超时（{timeout_seconds}秒）。\n\n"
                    f"项目名称：{project_name}\n"
                    f"任务状态：仍在RSHub服务器上执行中\n\n"
                    f"您可以稍后再次请求获取任务结果，或等待任务完成后重新查询。\n"
                    f"建议等待3-5分钟后重新请求任务结果。"
                )
                return (False, timeout_message)
            
            # 进度回报
            if session_id:
                try:
                    from ...api.progress import report_progress
                    progress_msg = f"任务执行中，已等待 {int(elapsed)}秒..."
                    report_progress(session_id, progress_msg, "processing", 
                                  {"elapsed_seconds": int(elapsed), "timeout_seconds": timeout_seconds})
                except ImportError:
                    pass
            
            import asyncio
            await asyncio.sleep(check_interval)
    
    @staticmethod
    async def check_task_error(token: str, project_name: str, task_name: str, 
                             scenario_name: str) -> str:
        """检查任务错误信息"""
        try:
            from rshub.load_file import load_file
            
            # 对于不同场景，使用不同的频率（这里使用默认值）
            default_freq = {
                'snow': 17.2,
                'soil': 1.26,
                'veg': 1.41
            }
            
            freq = default_freq.get(scenario_name, 1.0)
            
            data = load_file(token, project_name, task_name, freq)
            message = data.load_error_message()
            
            # 添加调试信息
            logger.info(f"检查任务错误信息: project={project_name}, task={task_name}, message={message}")
            
            # 如果load_error_message()返回None，但任务实际已完成，返回成功消息
            if message is None:
                # 尝试检查任务是否真的已完成
                try:
                    # 如果能够加载输出数据，说明任务成功完成
                    outputs = data.load_outputs()
                    if outputs:
                        logger.info(f"任务 {task_name} 已成功完成，但load_error_message()返回None")
                        return "Jobs completed succesfully"
                except Exception as load_ex:
                    logger.warning(f"无法加载任务输出: {str(load_ex)}")
                    # 如果无法加载输出，返回None以便上层处理
                    return "任务状态未知"
            
            return message
        except Exception as e:
            logger.error(f"检查错误信息失败: {str(e)}")
            return f"检查失败: {str(e)}"
    
    @staticmethod
    async def generate_task_summary(scenario_info: Dict, model_name: str,
                                 observation_modes: List[str], data_dicts: List[Dict],
                                 task_status: str, error_info: str,
                                 client: Any, session_id: Optional[str] = None) -> str:
        """生成任务总结"""
        from .. import langchain_prompts
        
        # 提取修改的参数
        modified_params = []
        for i, data in enumerate(data_dicts):
            params = []
            # 忽略一些系统参数
            ignore_keys = ['token', 'project_name', 'task_name', 'scenario_flag', 
                          'output_var', 'algorithm', 'level_required', 'force_update_flag']
            
            for key, value in data.items():
                if key not in ignore_keys:
                    params.append(f"{key}={value}")
            
            if params:
                modified_params.append(f"任务{i+1}: {', '.join(params[:5])}...")  # 只显示前5个参数
        
        modified_params_str = "\n".join(modified_params) if modified_params else "使用默认参数"
        
        template = langchain_prompts.RSHUB_TASK_SUMMARY_TEMPLATE
        variables = {
            "scenario": scenario_info['name_cn'],
            "model": MODEL_NAMES.get(model_name, model_name),
            "observation_modes": ", ".join(observation_modes),
            "modified_params": modified_params_str,
            "task_status": task_status,
            "error_info": error_info
        }
        
        messages = template.format_messages(**variables)
        system_msg = messages[0].content if len(messages) > 1 else None
        human_msg = messages[-1].content
        
        response = await client.generate_response(human_msg, system_msg)
        
        # 记录LLM调用计费
        try:
            from ...services.billing_tracker import get_billing_tracker
            billing_tracker = get_billing_tracker()
            billing_tracker.track_llm_call(session_id, "langchain", "task_summary_generation")
        except ImportError:
            pass
        
        return response