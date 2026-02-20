"""
计费跟踪模块 - 记录LLM调用和RSHub任务提交次数
"""

from typing import Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BillingTracker:
    """计费跟踪器"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
    
    def init_session(self, session_id: str) -> None:
        """初始化会话计费信息"""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "llm_calls": 0,
                "rshub_tasks": 0,
                "start_time": datetime.now(),
                "details": []
            }
            logger.info(f"初始化计费会话: {session_id}")
    
    def track_llm_call(self, session_id: str, model: str = None, purpose: str = None) -> None:
        """记录一次LLM调用"""
        self.init_session(session_id)
        self.sessions[session_id]["llm_calls"] += 1
        
        # 记录详情
        detail = {
            "type": "llm_call",
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "purpose": purpose
        }
        self.sessions[session_id]["details"].append(detail)
        
        logger.info(f"会话 {session_id} LLM调用次数: {self.sessions[session_id]['llm_calls']}")
    
    def track_rshub_task(self, session_id: str, task_name: str = None, project_name: str = None) -> None:
        """记录一次RSHub任务提交"""
        self.init_session(session_id)
        self.sessions[session_id]["rshub_tasks"] += 1
        
        # 记录详情
        detail = {
            "type": "rshub_task",
            "timestamp": datetime.now().isoformat(),
            "task_name": task_name,
            "project_name": project_name
        }
        self.sessions[session_id]["details"].append(detail)
        
        logger.info(f"会话 {session_id} RSHub任务数: {self.sessions[session_id]['rshub_tasks']}")
    
    def calculate_cost(self, session_id: str, llm_cost_factor: float = 1.0, 
                      rshub_cost_factor: float = 1.0) -> Dict:
        """计算会话总费用"""
        if session_id not in self.sessions:
            return {
                "llm_calls": 0,
                "rshub_tasks": 0,
                "llm_cost": 0.0,
                "rshub_cost": 0.0,
                "total_cost": 0.0,
                "duration_seconds": 0
            }
        
        session_data = self.sessions[session_id]
        llm_calls = session_data["llm_calls"]
        rshub_tasks = session_data["rshub_tasks"]
        
        llm_cost = llm_calls * llm_cost_factor
        rshub_cost = rshub_tasks * rshub_cost_factor
        total_cost = llm_cost + rshub_cost
        
        # 计算持续时间
        duration = (datetime.now() - session_data["start_time"]).total_seconds()
        
        result = {
            "llm_calls": llm_calls,
            "rshub_tasks": rshub_tasks,
            "llm_cost": llm_cost,
            "rshub_cost": rshub_cost,
            "total_cost": total_cost,
            "duration_seconds": duration,
            "details": session_data.get("details", [])
        }
        
        logger.info(f"会话 {session_id} 计费统计: LLM调用={llm_calls}, RSHub任务={rshub_tasks}, 总费用={total_cost}")
        
        return result
    
    def clear_session(self, session_id: str) -> None:
        """清除会话计费信息"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"清除计费会话: {session_id}")
    
    def get_all_sessions(self) -> Dict:
        """获取所有会话的计费信息"""
        return self.sessions.copy()

# 全局计费跟踪器实例
billing_tracker = BillingTracker()

def get_billing_tracker() -> BillingTracker:
    """获取计费跟踪器实例"""
    return billing_tracker 