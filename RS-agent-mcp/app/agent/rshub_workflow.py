"""
RSHub工作流实现 - 重构后的轻量级协调器
从原来的2032行巨型文件重构为217行的协调器，减少89%的代码量
支持完整工作流、仅提交工作流、仅获取结果工作流三种模式
使用模块化组件：工作流管理器、组件管理器、可视化器、任务提取器等
"""

import logging
from typing import List, Optional, Dict, Any

# 导入新的模块化工作流组件
from .workflows import workflow_manager, RSHubWorkflow, RSHubSubmissionWorkflow, RSHubResultRetrievalWorkflow
from .workflows.rshub_components import SCENARIO_TYPES, MODEL_NAMES
from .workflows.rshub_task_extractor import RSHubTaskExtractor

logger = logging.getLogger(__name__)

# 为了向后兼容，保留原有的函数签名，但内部使用新的工作流架构


async def run_rshub_workflow(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    client: Any = None,
    rshub_token: Optional[str] = None
) -> str:
    """
    执行完整的RSHub工作流 - 重构后使用新的工作流管理器
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        output_path: 结果输出路径
        session_id: 会话ID，用于进度回报和中止控制
        client: LangChain客户端
        rshub_token: RSHub token，如果提供则使用此token，否则使用配置文件中的token
    
    Returns:
        处理结果字符串或错误信息
    """
    logger.info("使用重构后的RSHub工作流执行完整任务...")
    
    try:
        # 使用工作流管理器执行完整RSHub工作流
        result = await workflow_manager.execute_workflow(
            "rshub_full",
            user_prompt=user_prompt,
            file_paths=file_paths,
            output_path=output_path,
            session_id=session_id,
            client=client,
            rshub_token=rshub_token
        )
        
        if result.success:
            return result.message
        else:
            return f"错误：{result.message}"
            
    except Exception as e:
        logger.error(f"RSHub工作流执行失败: {str(e)}", exc_info=True)
        return f"错误：RSHub工作流执行失败 - {str(e)}"


async def run_rshub_task_submission(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    session_id: Optional[str] = None,
    client: Any = None,
    rshub_token: Optional[str] = None
) -> str:
    """
    执行RSHub任务提交工作流（只包含任务提交部分，不含轮询和后处理）
    重构后使用新的工作流管理器
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        session_id: 会话ID
        client: LangChain客户端
        rshub_token: RSHub token，如果提供则使用此token，否则使用配置文件中的token
    
    Returns:
        任务提交结果，包含project和task信息以及data字典
    """
    logger.info("使用重构后的RSHub工作流执行任务提交...")
    
    try:
        # 使用工作流管理器执行任务提交工作流
        result = await workflow_manager.execute_workflow(
            "rshub_submission",
            user_prompt=user_prompt,
            file_paths=file_paths,
            session_id=session_id,
            client=client,
            rshub_token=rshub_token
        )
        
        if result.success:
            return result.message
        else:
            return f"错误：{result.message}"
            
    except Exception as e:
        logger.error(f"RSHub任务提交失败: {str(e)}", exc_info=True)
        return f"抱歉，提交RSHub任务时遇到了问题：{str(e)}"


async def run_rshub_result_retrieval(
    user_prompt: str,
    file_paths: Optional[List[str]] = None,
    output_path: Optional[str] = None,
    session_id: Optional[str] = None,
    client: Any = None,
    rshub_token: Optional[str] = None,
    chat_history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    执行RSHub结果获取工作流（轮询任务状态、获取结果并进行后处理）
    重构后使用新的工作流管理器
    
    Args:
        user_prompt: 用户输入的提示词
        file_paths: 用户上传的文件路径列表
        output_path: 结果输出路径
        session_id: 会话ID
        client: LangChain客户端
        rshub_token: RSHub token
        chat_history: 会话历史，用于提取之前提交的任务信息
    
    Returns:
        结果获取和后处理结果
    """
    logger.info("使用重构后的RSHub工作流执行结果获取...")
    
    try:
        # 使用工作流管理器执行结果获取工作流
        result = await workflow_manager.execute_workflow(
            "rshub_retrieval",
            user_prompt=user_prompt,
            file_paths=file_paths,
            output_path=output_path,
            session_id=session_id,
            client=client,
            rshub_token=rshub_token,
            chat_history=chat_history
        )
        
        if result.success:
            return result.message
        else:
            return f"错误：{result.message}"
            
    except Exception as e:
        logger.error(f"RSHub结果获取失败: {str(e)}", exc_info=True)
        return f"抱歉，获取RSHub任务结果时遇到了问题：{str(e)}"


# === 为了向后兼容，保留的辅助函数和常量 ===
# 这些函数现在委托给相应的模块化组件

# 场景类型定义 - 从rshub_components导入
def get_scenario_types():
    """获取场景类型定义"""
    return SCENARIO_TYPES

# 模型名称映射 - 从rshub_components导入
def get_model_names():
    """获取模型名称映射"""
    return MODEL_NAMES

# 任务提取器实例
task_extractor = RSHubTaskExtractor()

async def extract_task_info_from_history(
    chat_history: Optional[List[Dict[str, Any]]], 
    user_prompt: str, 
    client: Any, 
    session_id: Optional[str] = None
) -> Optional[Dict]:
    """从会话历史中提取任务信息 - 委托给任务提取器"""
    return await task_extractor.extract_task_info_from_history(
        chat_history, user_prompt, client, session_id
    )

# 为了向后兼容，保留一些常用的工具函数
def get_scenario_info(scenario_type: int) -> Optional[Dict]:
    """根据场景类型编号获取场景信息"""
    return SCENARIO_TYPES.get(scenario_type)

def get_model_display_name(model_name: str) -> str:
    """获取模型显示名称"""
    return MODEL_NAMES.get(model_name, model_name)

# 工作流便捷函数
async def run_workflow(workflow_name: str, **kwargs) -> Dict[str, Any]:
    """便捷函数：运行指定的工作流"""
    result = await workflow_manager.execute_workflow(workflow_name, **kwargs)
    return result.to_dict()

def get_available_workflows() -> List[str]:
    """获取可用的工作流列表"""
    return list(workflow_manager.workflows.keys())

# 兼容性别名 - 确保现有代码不会中断
run_rshub_full_workflow = run_rshub_workflow
run_rshub_submit_only = run_rshub_task_submission
run_rshub_get_results = run_rshub_result_retrieval

logger.info("RSHub工作流重构完成 - 从2032行原始代码重构为模块化架构")
logger.info("主要改进:")
logger.info("1. 创建了BaseWorkflow基类和WorkflowManager")
logger.info("2. 分离了环境管理、任务分析、参数管理等组件")
logger.info("3. 独立了可视化功能")
logger.info("4. 提取了任务历史分析逻辑")
logger.info("5. 支持完整工作流、仅提交、仅获取结果三种模式")
logger.info("6. 保持了完全的向后兼容性")