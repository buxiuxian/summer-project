"""
RSHub工作流实现 - 使用模块化组件重构后的主工作流
"""

import os
import json
import logging
import datetime
from typing import List, Optional, Dict, Any

from .base_workflow import BaseWorkflow, WorkflowResult, WorkflowContext
from .rshub_components import (
    RSHubEnvironmentManager, RSHubTaskAnalyzer, RSHubParameterManager, RSHubTaskManager
)
from .rshub_visualizer import RSHubVisualizer
from .rshub_task_extractor import RSHubTaskExtractor, RSHubSubmissionHelper

logger = logging.getLogger(__name__)


class RSHubWorkflow(BaseWorkflow):
    """RSHub工作流主类"""
    
    def __init__(self):
        super().__init__("RSHubWorkflow")
        self.env_manager = RSHubEnvironmentManager()
        self.task_analyzer = RSHubTaskAnalyzer()
        self.param_manager = RSHubParameterManager()
        self.task_manager = RSHubTaskManager()
        self.visualizer = RSHubVisualizer()
        self.task_extractor = RSHubTaskExtractor()
        self.submission_helper = RSHubSubmissionHelper()
    
    async def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required_params = ['user_prompt']
        return all(param in kwargs for param in required_params)
    
    async def execute(self, **kwargs) -> WorkflowResult:
        """执行完整的RSHub工作流"""
        user_prompt = kwargs.get('user_prompt', '')
        file_paths = kwargs.get('file_paths')
        output_path = kwargs.get('output_path')
        session_id = kwargs.get('session_id')
        client = kwargs.get('client')
        rshub_token = kwargs.get('rshub_token')
        
        try:
            self.start_timing()
            
            # 创建工作流上下文
            context = WorkflowContext({
                'user_prompt': user_prompt,
                'file_paths': file_paths,
                'output_path': output_path,
                'session_id': session_id,
                'client': client,
                'rshub_token': rshub_token
            })
            
            # 执行工作流步骤
            await self._execute_workflow_steps(context)
            
            # 生成结果
            result_data = context.get('result_data', {})
            plot_files = context.get('plot_files', [])
            final_message = context.get('final_message', '')
            
            elapsed_time = self.end_timing()
            return WorkflowResult(
                success=True,
                message=final_message,
                data=result_data,
                plot_files=plot_files,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            elapsed_time = self.end_timing()
            error_msg = f"RSHub工作流执行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return WorkflowResult(
                success=False,
                message=error_msg,
                elapsed_time=elapsed_time
            )
    
    async def _execute_workflow_steps(self, context: WorkflowContext):
        """执行工作流步骤"""
        session_id = context.get('session_id')
        
        # 步骤1: 检查RSHub环境
        await self._step_check_environment(context)
        
        # 步骤2: 分析任务配置
        await self._step_analyze_task(context)
        
        # 步骤3: 生成参数代码
        await self._step_generate_parameters(context)
        
        # 步骤4: 提交任务
        await self._step_submit_tasks(context)
        
        # 步骤5: 可选的日志记录
        if await self.submission_helper.should_generate_log(context.get('user_prompt', '')):
            await self._step_generate_log(context)
        
        # 步骤6: 等待任务完成
        await self._step_wait_completion(context)
        
        # 步骤7: 检查任务错误
        await self._step_check_errors(context)
        
        # 步骤8: 生成可视化结果
        await self._step_generate_visualization(context)
    
    async def _step_check_environment(self, context: WorkflowContext):
        """步骤1: 检查RSHub环境"""
        session_id = context.get('session_id')
        
        await self.report_progress(session_id, "正在检查RSHub环境...", "processing", 
                                 {"step": 1, "total_steps": 8})
        
        if not await self.env_manager.check_and_install_rshub(session_id):
            raise Exception("无法安装RSHub包，请检查网络连接")
        
        # 获取RSHub Token
        rshub_token = context.get('rshub_token')
        if rshub_token:
            token = rshub_token
        else:
            from ...core.config import settings
            token = settings.RSHUB_TOKEN
            if not token:
                raise Exception("未配置RSHUB_TOKEN，请在.env文件中设置")
        
        context.set('token', token)
    
    async def _step_analyze_task(self, context: WorkflowContext):
        """步骤2: 分析任务配置"""
        session_id = context.get('session_id')
        client = context.get('client')
        user_prompt = context.get('user_prompt', '')
        file_paths = context.get('file_paths')
        
        await self.report_progress(session_id, "正在分析任务类型...", "processing", 
                                 {"step": 2, "total_steps": 8})
        
        # 判断场景类型
        scenario_type = await self.task_analyzer.classify_scenario(
            user_prompt, file_paths, client, session_id
        )
        if scenario_type == -1:
            raise Exception("无法确定建模场景类型，请明确指定雪地、土壤或植被之一")
        
        from .rshub_components import SCENARIO_TYPES
        scenario_info = SCENARIO_TYPES[scenario_type]
        logger.info(f"确定场景类型: {scenario_info['name']} ({scenario_info['name_cn']})")
        
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        
        # 判断使用的模型
        model_name = await self.task_analyzer.select_model(
            scenario_type, user_prompt, client, session_id
        )
        logger.info(f"选择模型: {model_name}")
        
        # 判断观测模式
        observation_modes = await self.task_analyzer.determine_observation_modes(
            scenario_info['name'], user_prompt, client, session_id
        )
        logger.info(f"观测模式: {observation_modes}")
        
        # 生成project_name
        project_name = f"{scenario_info['name']}-{model_name}-{timestamp}"
        
        context.update({
            'scenario_type': scenario_type,
            'scenario_info': scenario_info,
            'model_name': model_name,
            'observation_modes': observation_modes,
            'project_name': project_name,
            'timestamp': timestamp
        })
    
    async def _step_generate_parameters(self, context: WorkflowContext):
        """步骤3: 生成参数代码"""
        session_id = context.get('session_id')
        client = context.get('client')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        observation_modes = context.get('observation_modes')
        user_prompt = context.get('user_prompt', '')
        file_paths = context.get('file_paths')
        
        await self.report_progress(session_id, "正在解析并生成参数代码...", "llm_call", 
                                 {"step": 3, "total_steps": 8, "model": "langchain"})
        
        # 读取技术文档
        technical_docs = await self.param_manager.load_technical_docs(scenario_info['name'])
        
        # 读取用户上传的文件内容
        file_content = await self.param_manager.read_user_files(file_paths)
        
        # 生成参数代码
        param_code = await self.param_manager.generate_parameter_code(
            scenario_info, model_name, observation_modes, 
            user_prompt, file_content, technical_docs, 
            client, session_id
        )
        
        if not param_code:
            raise Exception("无法生成参数代码")
        
        logger.info(f"生成的参数代码:\n{param_code}")
        
        # 执行参数代码
        import numpy as np
        exec_globals = {
            'np': np,
            'datetime': datetime,
            'copy': __import__('copy')
        }
        
        exec(param_code, exec_globals)
        
        context.set('param_code', param_code)
        context.set('exec_globals', exec_globals)
    
    async def _step_submit_tasks(self, context: WorkflowContext):
        """步骤4: 提交任务到RSHub"""
        session_id = context.get('session_id')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        observation_modes = context.get('observation_modes')
        project_name = context.get('project_name')
        timestamp = context.get('timestamp')
        exec_globals = context.get('exec_globals')
        token = context.get('token')
        
        await self.report_progress(session_id, "正在提交任务到RSHub...", "processing", 
                                 {"step": 4, "total_steps": 8})
        
        # 检测参数字典数量并创建任务
        tasks = self.submission_helper.detect_param_count_and_create_tasks(
            exec_globals, scenario_info, model_name, observation_modes, timestamp, project_name
        )
        
        logger.info(f"创建的任务数量: {len(tasks)}")
        for i, task in enumerate(tasks):
            logger.info(f"任务{i+1}: {task['name']}")
        
        # 提取数据字典
        data_dicts = self.param_manager.extract_data_dicts_from_globals(exec_globals, len(tasks))
        
        if not data_dicts:
            raise Exception("参数代码执行后未生成有效的data字典")
        
        # 添加系统参数到数据字典
        for i, data_dict in enumerate(data_dicts):
            data_dict['token'] = token
            data_dict['project_name'] = project_name
            data_dict['task_name'] = tasks[i]['name']
            data_dict['scenario_flag'] = scenario_info['name']
            data_dict['algorithm'] = model_name
            data_dict['level_required'] = 1
            
            # 确保output_var使用正确格式
            if 'output_var' not in data_dict:
                data_dict['output_var'] = tasks[i]['output_var']
        
        # 提交任务
        try:
            from rshub import submit_jobs
        except ImportError:
            raise Exception("RSHub包导入失败")
        
        submission_results = []
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            submission_results = []
            all_success = True
            error_messages = []
            
            for i, data_dict in enumerate(data_dicts):
                try:
                    result = submit_jobs.run(data_dict)
                    submission_results.append(result)
                    
                    # 记录RSHub任务提交计费
                    session_id = context.get('session_id')
                    if session_id:
                        try:
                            from ...services.billing.billing_tracker import get_billing_tracker
                            billing_tracker = get_billing_tracker()
                            billing_tracker.track_rshub_task(
                                session_id, 
                                task_name=data_dict.get('task_name'),
                                project_name=data_dict.get('project_name')
                            )
                        except ImportError:
                            pass
                    
                    if result.get('result') != 'Job submitted!':
                        all_success = False
                        error_messages.append(f"任务{i+1}: {result}")
                        logger.error(f"任务提交失败: {result}")
                except Exception as e:
                    all_success = False
                    error_messages.append(f"任务{i+1}: {str(e)}")
                    logger.error(f"任务提交异常: {str(e)}")
            
            if all_success:
                break
            
            # 如果失败且还有重试次数
            if retry_count < max_retries:
                if session_id:
                    await self.report_progress(session_id, 
                                             f"任务提交失败，正在重新生成代码（第{retry_count+1}次重试）...", 
                                             "processing", 
                                             {"step": 4, "total_steps": 8, "retry": retry_count+1})
                
                # 使用LLM分析错误并重新生成代码
                error_info = "\n".join(error_messages)
                param_code = context.get('param_code')
                scenario_type = scenario_info['name']
                client = context.get('client')
                
                param_code = await self.param_manager.fix_parameter_code(
                    error_info, param_code, scenario_type, client, session_id
                )
                
                if param_code:
                    # 重新执行参数代码
                    import numpy as np
                    exec_globals = {
                        'np': np,
                        'datetime': datetime,
                        'copy': __import__('copy')
                    }
                    
                    exec(param_code, exec_globals)
                    
                    # 重新提取data字典
                    data_dicts = []
                    extracted_data = self.param_manager.extract_data_dicts_from_globals(exec_globals, len(tasks))
                    
                    for i, data_dict in enumerate(extracted_data):
                        # 添加系统必需参数
                        data_dict['token'] = token
                        data_dict['project_name'] = project_name
                        data_dict['task_name'] = tasks[i]['name']
                        data_dict['scenario_flag'] = scenario_info['name']
                        data_dict['algorithm'] = model_name
                        data_dict['level_required'] = 1
                        
                        # 确保output_var使用正确格式
                        if 'output_var' not in data_dict:
                            data_dict['output_var'] = tasks[i]['output_var']
                        
                        data_dicts.append(data_dict)
            
            retry_count += 1
        
        if not all_success:
            error_summary = "\n".join(error_messages)
            raise Exception(f"任务提交失败。\n{error_summary}")
        
        context.update({
            'tasks': tasks,
            'data_dicts': data_dicts
        })
    
    async def _step_generate_log(self, context: WorkflowContext):
        """步骤5: 生成日志"""
        session_id = context.get('session_id')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        data_dicts = context.get('data_dicts')
        
        await self.report_progress(session_id, "正在生成日志...", "processing", 
                                 {"step": 5, "total_steps": 8})
        
        await self.submission_helper.generate_log(project_name, tasks, data_dicts)
    
    async def _step_wait_completion(self, context: WorkflowContext):
        """步骤6: 等待任务完成"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        
        await self.report_progress(session_id, "正在等待RSHub处理任务...", "processing", 
                                 {"step": 6, "total_steps": 8})
        
        # 等待所有任务完成
        task_success, failure_reason = await self.task_manager.wait_for_tasks(
            token, project_name, tasks, session_id
        )
        
        if not task_success:
            if "RSHub服务器任务失败" in failure_reason:
                raise Exception(f"{failure_reason}。问题出现在RSHub服务器端，请稍后重试或联系技术支持。")
            else:
                raise Exception(f"任务执行失败 - {failure_reason}")
    
    async def _step_check_errors(self, context: WorkflowContext):
        """步骤7: 检查任务错误"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        scenario_info = context.get('scenario_info')
        
        await self.report_progress(session_id, "正在检查任务执行结果...", "processing", 
                                 {"step": 7, "total_steps": 8})
        
        task_errors = []
        for task in tasks:
            error_msg = await self.task_manager.check_task_error(
                token, project_name, task['name'], scenario_info['name']
            )
            if error_msg and "Jobs completed succesfully" not in error_msg:
                task_errors.append(f"{task['name']}: {error_msg}")
        
        if task_errors:
            error_summary = "\n".join(task_errors)
            raise Exception(f"任务执行失败。\n{error_summary}")
    
    async def _step_generate_visualization(self, context: WorkflowContext):
        """步骤8: 生成可视化结果"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        data_dicts = context.get('data_dicts')
        output_path = context.get('output_path')
        client = context.get('client')
        
        await self.report_progress(session_id, "正在生成结果图表...", "processing", 
                                 {"step": 8, "total_steps": 8})
        
        # 获取结果并生成图表
        plot_files = await self.visualizer.generate_plots(
            token, project_name, tasks, scenario_info, model_name, 
            data_dicts, output_path
        )
        
        # 生成任务总结
        summary = await self.task_manager.generate_task_summary(
            scenario_info, model_name, context.get('observation_modes'), data_dicts, 
            "成功", "", client, session_id
        )
        
        # 构建最终结果
        result = f"{summary}\n\n"
        
        if plot_files:
            result += "## 建模结果图表\n\n"
            for file_path in plot_files:
                # 获取文件名
                filename = os.path.basename(file_path)
                # 生成前端访问URL，需要匹配FastAPI的静态文件挂载路径
                # file_path形如 "temp/filename.png"，需要转换为 "/temp/filename.png"
                if file_path.startswith("temp"):
                    # 如果路径以temp开头，添加前缀斜杠
                    url_path = "/" + file_path.replace("\\", "/")
                else:
                    # 如果路径不是以temp开头，使用完整路径
                    url_path = file_path.replace("\\", "/")
                
                # 添加图片显示标记，前端可以识别并显示
                result += f"![{filename}]({url_path})\n"
            result += "\n"
        
        elapsed_time = context.get('elapsed_time', 0)
        if elapsed_time > 0:
            result += f"**总耗时：{elapsed_time:.1f}秒**"
        
        context.update({
            'plot_files': plot_files,
            'final_message': result,
            'result_data': {
                'project_name': project_name,
                'scenario_info': scenario_info,
                'model_name': model_name,
                'observation_modes': context.get('observation_modes'),
                'tasks': tasks,
                'data_dicts': data_dicts
            }
        })


class RSHubSubmissionWorkflow(BaseWorkflow):
    """RSHub任务提交工作流（仅提交，不等待结果）"""
    
    def __init__(self):
        super().__init__("RSHubSubmissionWorkflow")
        self.env_manager = RSHubEnvironmentManager()
        self.task_analyzer = RSHubTaskAnalyzer()
        self.param_manager = RSHubParameterManager()
        self.submission_helper = RSHubSubmissionHelper()
    
    async def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required_params = ['user_prompt']
        return all(param in kwargs for param in required_params)
    
    async def execute(self, **kwargs) -> WorkflowResult:
        """执行任务提交工作流"""
        user_prompt = kwargs.get('user_prompt', '')
        file_paths = kwargs.get('file_paths')
        session_id = kwargs.get('session_id')
        client = kwargs.get('client')
        rshub_token = kwargs.get('rshub_token')
        
        try:
            self.start_timing()
            
            # 创建工作流上下文
            context = WorkflowContext({
                'user_prompt': user_prompt,
                'file_paths': file_paths,
                'session_id': session_id,
                'client': client,
                'rshub_token': rshub_token
            })
            
            # 执行简化的工作流步骤
            await self._execute_submission_steps(context)
            
            # 生成结果
            result_data = context.get('result_data', {})
            final_message = context.get('final_message', '')
            
            elapsed_time = self.end_timing()
            return WorkflowResult(
                success=True,
                message=final_message,
                data=result_data,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            elapsed_time = self.end_timing()
            error_msg = f"RSHub任务提交失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return WorkflowResult(
                success=False,
                message=error_msg,
                elapsed_time=elapsed_time
            )
    
    async def _execute_submission_steps(self, context: WorkflowContext):
        """执行任务提交步骤"""
        session_id = context.get('session_id')
        
        # 步骤1: 检查RSHub环境
        await self._step_check_environment(context)
        
        # 步骤2: 分析任务配置
        await self._step_analyze_task(context)
        
        # 步骤3: 生成参数代码
        await self._step_generate_parameters(context)
        
        # 步骤4: 提交任务
        await self._step_submit_tasks(context)
        
        # 步骤5: 生成提交结果消息
        await self._step_generate_result(context)
    
    # 这些方法与主工作流类似，但简化了流程
    async def _step_check_environment(self, context: WorkflowContext):
        """检查RSHub环境"""
        session_id = context.get('session_id')
        
        await self.report_progress(session_id, "正在检查RSHub环境...", "processing", 
                                 {"step": 1, "total_steps": 5})
        
        if not await self.env_manager.check_and_install_rshub(session_id):
            raise Exception("无法安装RSHub包，请检查网络连接")
        
        # 获取RSHub Token
        rshub_token = context.get('rshub_token')
        if rshub_token:
            token = rshub_token
        else:
            from ...core.config import settings
            token = settings.RSHUB_TOKEN
            if not token:
                raise Exception("未配置RSHUB_TOKEN，请在.env文件中设置")
        
        context.set('token', token)
    
    async def _step_analyze_task(self, context: WorkflowContext):
        """分析任务配置"""
        session_id = context.get('session_id')
        client = context.get('client')
        user_prompt = context.get('user_prompt', '')
        file_paths = context.get('file_paths')
        
        await self.report_progress(session_id, "正在分析任务类型...", "processing", 
                                 {"step": 2, "total_steps": 5})
        
        # 判断场景类型
        scenario_type = await self.task_analyzer.classify_scenario(
            user_prompt, file_paths, client, session_id
        )
        if scenario_type == -1:
            raise Exception("无法确定建模场景类型，请明确指定雪地、土壤或植被之一")
        
        from .rshub_components import SCENARIO_TYPES
        scenario_info = SCENARIO_TYPES[scenario_type]
        
        # 生成时间戳
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
        
        # 判断使用的模型
        model_name = await self.task_analyzer.select_model(
            scenario_type, user_prompt, client, session_id
        )
        
        # 判断观测模式
        observation_modes = await self.task_analyzer.determine_observation_modes(
            scenario_info['name'], user_prompt, client, session_id
        )
        
        # 生成project_name
        project_name = f"{scenario_info['name']}-{model_name}-{timestamp}"
        
        context.update({
            'scenario_type': scenario_type,
            'scenario_info': scenario_info,
            'model_name': model_name,
            'observation_modes': observation_modes,
            'project_name': project_name,
            'timestamp': timestamp
        })
    
    async def _step_generate_parameters(self, context: WorkflowContext):
        """生成参数代码"""
        session_id = context.get('session_id')
        client = context.get('client')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        observation_modes = context.get('observation_modes')
        user_prompt = context.get('user_prompt', '')
        file_paths = context.get('file_paths')
        
        await self.report_progress(session_id, "正在解析并生成参数代码...", "llm_call", 
                                 {"step": 3, "total_steps": 5, "model": "langchain"})
        
        # 读取技术文档
        technical_docs = await self.param_manager.load_technical_docs(scenario_info['name'])
        
        # 读取用户上传的文件内容
        file_content = await self.param_manager.read_user_files(file_paths)
        
        # 生成参数代码
        param_code = await self.param_manager.generate_parameter_code(
            scenario_info, model_name, observation_modes, 
            user_prompt, file_content, technical_docs, 
            client, session_id
        )
        
        if not param_code:
            raise Exception("无法生成参数代码")
        
        # 执行参数代码
        import numpy as np
        exec_globals = {
            'np': np,
            'datetime': datetime,
            'copy': __import__('copy')
        }
        
        exec(param_code, exec_globals)
        
        context.set('param_code', param_code)
        context.set('exec_globals', exec_globals)
    
    async def _step_submit_tasks(self, context: WorkflowContext):
        """提交任务"""
        session_id = context.get('session_id')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        observation_modes = context.get('observation_modes')
        project_name = context.get('project_name')
        timestamp = context.get('timestamp')
        exec_globals = context.get('exec_globals')
        token = context.get('token')
        
        await self.report_progress(session_id, "正在提交RSHub计算任务...", "processing", 
                                 {"step": 4, "total_steps": 5})
        
        # 检测参数字典数量并创建任务
        tasks = self.submission_helper.detect_param_count_and_create_tasks(
            exec_globals, scenario_info, model_name, observation_modes, timestamp, project_name
        )
        
        # 提取数据字典
        data_dicts = self.param_manager.extract_data_dicts_from_globals(exec_globals, len(tasks))
        
        if not data_dicts:
            raise Exception("无法从参数代码中提取数据字典")
        
        # 设置每个数据字典的固定参数
        for i, data_dict in enumerate(data_dicts):
            data_dict['scenario_flag'] = scenario_info['name']
            data_dict['algorithm'] = model_name
            data_dict['project_name'] = project_name
            data_dict['task_name'] = tasks[i]['name']
            data_dict['token'] = token
            data_dict['force_update_flag'] = 1
            data_dict['level_required'] = 1
            if 'core_num' not in data_dict:
                data_dict['core_num'] = 2
            
            # 设置output_var
            if 'output_var' not in data_dict:
                data_dict['output_var'] = tasks[i]['output_var']
        
        # 导入rshub模块
        try:
            from rshub import submit_jobs
        except ImportError:
            raise Exception("无法导入rshub模块，请检查安装")
        
        # 提交所有任务
        submission_results = []
        for i, data_dict in enumerate(data_dicts):
            try:
                result = submit_jobs.run(data_dict)
                submission_results.append(result)
                logger.info(f"任务 {i+1} 提交结果: {result}")
                
                # 记录RSHub任务提交计费
                session_id = context.get('session_id')
                if session_id:
                    try:
                        from ...services.billing.billing_tracker import get_billing_tracker
                        billing_tracker = get_billing_tracker()
                        billing_tracker.track_rshub_task(
                            session_id, 
                            task_name=data_dict.get('task_name'),
                            project_name=data_dict.get('project_name')
                        )
                    except ImportError:
                        pass
            except Exception as e:
                logger.error(f"任务 {i+1} 提交失败: {str(e)}")
                submission_results.append({'result': f'Error: {str(e)}'})
        
        # 检查提交结果
        failed_tasks = []
        for i, result in enumerate(submission_results):
            if result.get('result') != 'Job submitted!':
                failed_tasks.append(f"任务 {i+1}: {result.get('result', '未知错误')}")
        
        if failed_tasks:
            raise Exception(f"任务提交失败：\n" + "\n".join(failed_tasks))
        
        context.update({
            'tasks': tasks,
            'data_dicts': data_dicts
        })
    
    async def _step_generate_result(self, context: WorkflowContext):
        """生成提交结果消息"""
        project_name = context.get('project_name')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        observation_modes = context.get('observation_modes')
        tasks = context.get('tasks')
        data_dicts = context.get('data_dicts')
        timestamp = context.get('timestamp')
        
        from .rshub_components import MODEL_NAMES
        
        # 所有任务提交成功，生成回报信息
        success_message = f"✅ RSHub建模任务提交成功！\n\n"
        success_message += f"**项目名称**: {project_name}\n"
        success_message += f"**场景类型**: {scenario_info['name_cn']} ({scenario_info['name']})\n"
        success_message += f"**使用模型**: {MODEL_NAMES[model_name]}\n"
        success_message += f"**观测模式**: {', '.join(observation_modes)}\n"
        success_message += f"**任务数量**: {len(tasks)}\n\n"
        
        success_message += "**提交的任务列表**:\n"
        for i, task in enumerate(tasks):
            success_message += f"{i+1}. {task['name']}\n"
        
        success_message += "\n**提示**: 任务正在RSHub服务器上计算中，通常需要几分钟到几小时完成。"
        success_message += "计算完成后，您可以在同一会话中询问\"请获取刚才计算任务的结果并为我可视化\"来获取结果。\n\n"
        
        # 添加完整的data字典信息（用于mode3提取）
        success_message += "**任务详细信息**:\n"
        success_message += "```json\n"
        success_message += json.dumps({
            'project_name': project_name,
            'scenario_info': scenario_info,
            'model_name': model_name,
            'observation_modes': observation_modes,
            'tasks': tasks,
            'data_dicts': data_dicts,
            'timestamp': timestamp
        }, indent=2, ensure_ascii=False)
        success_message += "\n```"
        
        context.update({
            'final_message': success_message,
            'result_data': {
                'project_name': project_name,
                'scenario_info': scenario_info,
                'model_name': model_name,
                'observation_modes': observation_modes,
                'tasks': tasks,
                'data_dicts': data_dicts,
                'timestamp': timestamp
            }
        })


class RSHubResultRetrievalWorkflow(BaseWorkflow):
    """RSHub结果获取工作流"""
    
    def __init__(self):
        super().__init__("RSHubResultRetrievalWorkflow")
        self.task_extractor = RSHubTaskExtractor()
        self.task_manager = RSHubTaskManager()
        self.visualizer = RSHubVisualizer()
    
    async def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        required_params = ['user_prompt', 'chat_history']
        return all(param in kwargs for param in required_params)
    
    async def execute(self, **kwargs) -> WorkflowResult:
        """执行结果获取工作流"""
        user_prompt = kwargs.get('user_prompt', '')
        file_paths = kwargs.get('file_paths')
        output_path = kwargs.get('output_path')
        session_id = kwargs.get('session_id')
        client = kwargs.get('client')
        rshub_token = kwargs.get('rshub_token')
        chat_history = kwargs.get('chat_history')
        
        try:
            self.start_timing()
            
            # 创建工作流上下文
            context = WorkflowContext({
                'user_prompt': user_prompt,
                'file_paths': file_paths,
                'output_path': output_path,
                'session_id': session_id,
                'client': client,
                'rshub_token': rshub_token,
                'chat_history': chat_history
            })
            
            # 执行结果获取步骤
            await self._execute_retrieval_steps(context)
            
            # 生成结果
            result_data = context.get('result_data', {})
            final_message = context.get('final_message', '')
            
            elapsed_time = self.end_timing()
            return WorkflowResult(
                success=True,
                message=final_message,
                data=result_data,
                elapsed_time=elapsed_time
            )
            
        except Exception as e:
            elapsed_time = self.end_timing()
            error_msg = f"RSHub结果获取失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return WorkflowResult(
                success=False,
                message=error_msg,
                elapsed_time=elapsed_time
            )
    
    async def _execute_retrieval_steps(self, context: WorkflowContext):
        """执行结果获取步骤"""
        session_id = context.get('session_id')
        
        # 步骤1: 从会话历史中提取任务信息
        await self._step_extract_task_info(context)
        
        # 步骤2: 轮询任务状态
        await self._step_wait_tasks(context)
        
        # 步骤3: 检查任务错误
        await self._step_check_task_errors(context)
        
        # 步骤4: 生成可视化结果
        await self._step_generate_results(context)
    
    async def _step_extract_task_info(self, context: WorkflowContext):
        """从会话历史中提取任务信息"""
        session_id = context.get('session_id')
        chat_history = context.get('chat_history')
        user_prompt = context.get('user_prompt', '')
        client = context.get('client')
        
        await self.report_progress(session_id, "正在从会话历史中查找任务信息...", "processing", 
                                 {"step": 1, "total_steps": 4})
        
        # 检查是否有会话历史
        if not chat_history:
            logger.warning("没有会话历史，无法提取任务信息")
            await self.report_progress(session_id, "检测到无会话历史，建议用户先提交建模任务", "warning")
            raise Exception("没有找到之前的任务记录。请先提交一个RSHub建模任务，然后再尝试获取结果。")
        
        task_info = await self.task_extractor.extract_task_info_from_history(
            chat_history, user_prompt, client, session_id
        )
        
        if not task_info:
            logger.warning("无法从会话历史中提取任务信息")
            await self.report_progress(session_id, "未找到相关任务信息，建议重新提交任务", "warning")
            raise Exception("在会话历史中未找到相关的RSHub任务信息。请确认您之前成功提交了任务，或者重新提交一个新任务。")
        
        # 获取任务详细信息
        project_name = task_info['project_name']
        scenario_info = task_info['scenario_info']
        model_name = task_info['model_name']
        observation_modes = task_info['observation_modes']
        tasks = task_info['tasks']
        data_dicts = task_info['data_dicts']
        
        # 获取RSHub Token
        rshub_token = context.get('rshub_token')
        if rshub_token:
            token = rshub_token
        else:
            from ...core.config import settings
            token = settings.RSHUB_TOKEN
            if not token:
                raise Exception("未配置RSHUB_TOKEN，请在.env文件中设置")
        
        context.update({
            'token': token,
            'project_name': project_name,
            'scenario_info': scenario_info,
            'model_name': model_name,
            'observation_modes': observation_modes,
            'tasks': tasks,
            'data_dicts': data_dicts
        })
    
    async def _step_wait_tasks(self, context: WorkflowContext):
        """轮询任务状态"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        
        await self.report_progress(session_id, f"正在检查任务状态: {project_name}...", "processing", 
                                 {"step": 2, "total_steps": 4})
        
        success, error_message = await self.task_manager.wait_for_tasks(
            token, project_name, tasks, session_id
        )
        
        if not success:
            raise Exception(f"任务执行失败：{error_message}")
    
    async def _step_check_task_errors(self, context: WorkflowContext):
        """检查任务错误"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        scenario_info = context.get('scenario_info')
        
        await self.report_progress(session_id, "正在检查任务执行结果...", "processing", 
                                 {"step": 3, "total_steps": 4})
        
        for task in tasks:
            error_msg = await self.task_manager.check_task_error(
                token, project_name, task['name'], scenario_info['name']
            )
            # 使用与原始工作流相同的检查逻辑：如果有错误消息且不包含成功标识，则认为失败
            if error_msg and "Jobs completed succesfully" not in error_msg:
                raise Exception(f"任务 {task['name']} 执行失败：{error_msg}")
    
    async def _step_generate_results(self, context: WorkflowContext):
        """生成可视化结果"""
        session_id = context.get('session_id')
        token = context.get('token')
        project_name = context.get('project_name')
        tasks = context.get('tasks')
        scenario_info = context.get('scenario_info')
        model_name = context.get('model_name')
        data_dicts = context.get('data_dicts')
        output_path = context.get('output_path')
        client = context.get('client')
        
        await self.report_progress(session_id, "正在生成可视化结果...", "processing", 
                                 {"step": 4, "total_steps": 4})
        
        # 后处理：获取并可视化结果
        plot_files = await self.visualizer.generate_plots(
            token, project_name, tasks, scenario_info, model_name, data_dicts, output_path
        )
        
        # 生成任务总结
        task_summary = await self.task_manager.generate_task_summary(
            scenario_info, model_name, context.get('observation_modes'), data_dicts, 
            "成功完成", "", client, session_id
        )
        
        # 组装最终结果
        result_message = f"✅ RSHub任务结果获取成功！\n\n"
        result_message += task_summary
        
        if plot_files:
            result_message += f"\n\n## 建模结果图表\n\n"
            for file_path in plot_files:
                # 获取文件名
                filename = os.path.basename(file_path)
                # 生成前端访问URL，需要匹配FastAPI的静态文件挂载路径
                # file_path形如 "temp/filename.png"，需要转换为 "/temp/filename.png"
                if file_path.startswith("temp"):
                    # 如果路径以temp开头，添加前缀斜杠
                    url_path = "/" + file_path.replace("\\", "/")
                else:
                    # 如果路径不是以temp开头，使用完整路径
                    url_path = file_path.replace("\\", "/")
                
                # 添加图片显示标记，前端可以识别并显示
                result_message += f"![{filename}]({url_path})\n"
            result_message += "\n"
        
        context.update({
            'plot_files': plot_files,
            'final_message': result_message,
            'result_data': {
                'project_name': project_name,
                'scenario_info': scenario_info,
                'model_name': model_name,
                'observation_modes': context.get('observation_modes'),
                'tasks': tasks,
                'data_dicts': data_dicts
            }
        })