"""
Agent工作流模块
"""

from .base_workflow import BaseWorkflow, WorkflowManager, workflow_manager
from .rshub_workflow_impl import RSHubWorkflow, RSHubSubmissionWorkflow, RSHubResultRetrievalWorkflow
from .rshub_components import RSHubEnvironmentManager, RSHubTaskAnalyzer, RSHubParameterManager, RSHubTaskManager
from .rshub_visualizer import RSHubVisualizer
from .rshub_task_extractor import RSHubTaskExtractor, RSHubSubmissionHelper

# 注册工作流
workflow_manager.register_workflow("rshub_full", RSHubWorkflow())
workflow_manager.register_workflow("rshub_submission", RSHubSubmissionWorkflow())
workflow_manager.register_workflow("rshub_retrieval", RSHubResultRetrievalWorkflow())

__all__ = [
    "BaseWorkflow",
    "WorkflowManager", 
    "workflow_manager",
    "RSHubWorkflow",
    "RSHubSubmissionWorkflow", 
    "RSHubResultRetrievalWorkflow",
    "RSHubEnvironmentManager",
    "RSHubTaskAnalyzer",
    "RSHubParameterManager",
    "RSHubTaskManager",
    "RSHubVisualizer",
    "RSHubTaskExtractor",
    "RSHubSubmissionHelper"
]