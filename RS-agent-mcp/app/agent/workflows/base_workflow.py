"""
工作流基类和通用模式 - 为RSHub工作流提供基础架构
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowResult:
    """工作流执行结果"""
    
    def __init__(self, success: bool = False, message: str = "", 
                 data: Optional[Dict] = None, plot_files: Optional[List[str]] = None, elapsed_time: float = 0.0):
        self.success = success
        self.message = message
        self.data = data or {}
        self.plot_files = plot_files or []
        self.timestamp = datetime.now()
        self.elapsed_time = elapsed_time
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "plot_files": self.plot_files,
            "timestamp": self.timestamp.isoformat(),
            "elapsed_time": self.elapsed_time
        }


class BaseWorkflow(ABC):
    """工作流基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.start_time = None
        self.end_time = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> WorkflowResult:
        """执行工作流"""
        pass
    
    @abstractmethod
    async def validate_inputs(self, **kwargs) -> bool:
        """验证输入参数"""
        pass
    
    def start_timing(self):
        """开始计时"""
        self.start_time = datetime.now()
    
    def end_timing(self) -> float:
        """结束计时并返回耗时（秒）"""
        if self.start_time:
            self.end_time = datetime.now()
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    async def report_progress(self, session_id: Optional[str], message: str, 
                            stage: str, metadata: Optional[Dict] = None):
        """报告进度（如果可用）"""
        try:
            from ...api.progress import report_progress
            if session_id:
                report_progress(session_id, message, stage, metadata)
        except ImportError:
            pass
    
    def is_session_aborted(self, session_id: Optional[str]) -> bool:
        """检查会话是否被中止"""
        try:
            from ...api.progress import is_session_aborted
            if session_id:
                return is_session_aborted(session_id)
        except ImportError:
            pass
        return False
    
    async def cleanup_temp_directory(self):
        """清理临时目录"""
        try:
            import os
            temp_dir = "temp"
            if os.path.exists(temp_dir):
                for file in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, file)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.logger.info(f"已清理临时文件: {file_path}")
            else:
                os.makedirs(temp_dir, exist_ok=True)
                self.logger.info("已创建temp目录")
        except Exception as e:
            self.logger.error(f"清理temp目录失败: {str(e)}")


class WorkflowStep:
    """工作流步骤"""
    
    def __init__(self, name: str, step_number: int, total_steps: int):
        self.name = name
        self.step_number = step_number
        self.total_steps = total_steps
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行步骤"""
        self.logger.info(f"开始执行步骤 {self.step_number}/{self.total_steps}: {self.name}")
        
        # 报告进度
        session_id = context.get('session_id')
        if session_id:
            await self._report_progress(session_id, f"正在{self.name}...", "processing")
        
        # 执行具体逻辑
        try:
            result = await self._execute_step(context)
            self.logger.info(f"步骤 {self.step_number}/{self.total_steps} 完成: {self.name}")
            return result
        except Exception as e:
            self.logger.error(f"步骤 {self.step_number}/{self.total_steps} 失败: {self.name} - {str(e)}")
            raise
    
    @abstractmethod
    async def _execute_step(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体步骤逻辑"""
        pass
    
    def _report_progress(self, session_id: str, message: str, stage: str, 
                        metadata: Optional[Dict] = None):
        """报告进度"""
        try:
            from ...api.progress import report_progress
            metadata = metadata or {}
            metadata.update({
                "step": self.step_number,
                "total_steps": self.total_steps
            })
            report_progress(session_id, message, stage, metadata)
        except ImportError:
            pass


class WorkflowContext:
    """工作流上下文管理器"""
    
    def __init__(self, initial_context: Optional[Dict] = None):
        self.context = initial_context or {}
        self.history = []
    
    def get(self, key: str, default=None):
        """获取上下文值"""
        return self.context.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置上下文值"""
        self.context[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新上下文"""
        self.context.update(updates)
    
    def add_history(self, entry: Dict[str, Any]):
        """添加历史记录"""
        entry['timestamp'] = datetime.now()
        self.history.append(entry)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "context": self.context,
            "history": self.history
        }


class WorkflowManager:
    """工作流管理器"""
    
    def __init__(self):
        self.workflows: Dict[str, BaseWorkflow] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_workflow(self, name: str, workflow: BaseWorkflow):
        """注册工作流"""
        self.workflows[name] = workflow
        self.logger.info(f"已注册工作流: {name}")
    
    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """获取工作流"""
        return self.workflows.get(name)
    
    async def execute_workflow(self, name: str, **kwargs) -> WorkflowResult:
        """执行指定工作流"""
        workflow = self.get_workflow(name)
        if not workflow:
            error_msg = f"未找到工作流: {name}"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, message=error_msg)
        
        # 验证输入
        if not await workflow.validate_inputs(**kwargs):
            error_msg = f"工作流 {name} 输入验证失败"
            self.logger.error(error_msg)
            return WorkflowResult(success=False, message=error_msg)
        
        # 执行工作流
        workflow.start_timing()
        try:
            result = await workflow.execute(**kwargs)
            elapsed_time = workflow.end_timing()
            result.elapsed_time = elapsed_time
            
            if result.success:
                self.logger.info(f"工作流 {name} 执行成功，耗时: {elapsed_time:.1f}秒")
            else:
                self.logger.error(f"工作流 {name} 执行失败，耗时: {elapsed_time:.1f}秒")
            
            return result
        except Exception as e:
            elapsed_time = workflow.end_timing()
            error_msg = f"工作流 {name} 执行异常: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return WorkflowResult(success=False, message=error_msg, elapsed_time=elapsed_time)


# 全局工作流管理器实例
workflow_manager = WorkflowManager()