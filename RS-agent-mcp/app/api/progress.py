"""
进度回报API - 提供Agent执行进度的实时推送功能

该模块为前端提供Agent执行过程中的详细进度信息，让用户能够了解AI正在执行的具体步骤。

使用方法：
1. 前端通过SSE连接到 /progress/stream/{session_id} 接口
2. Agent执行过程中调用 report_progress() 函数发送进度消息
3. 前端实时接收并显示进度信息

扩展指南：
当添加新的Agent功能时，请在关键步骤调用 report_progress() 函数：
- 任务开始时：report_progress(session_id, "正在初始化新任务...", "init")
- LLM调用前：report_progress(session_id, "正在调用AI模型分析...", "llm_call")
- 数据处理时：report_progress(session_id, "正在处理数据...", "processing")
- 任务完成时：report_progress(session_id, "任务完成", "completed")
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, AsyncGenerator
from collections import defaultdict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# 配置日志
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/progress", tags=["progress"])

# 全局进度存储：{session_id: [progress_messages]}
progress_storage: Dict[str, list] = defaultdict(list)

# 活跃的SSE连接：{session_id: set(connection_ids)}
active_connections: Dict[str, set] = defaultdict(set)

# 中止请求标记：{session_id: bool}
abort_flags: Dict[str, bool] = {}

class ProgressReporter:
    """
    进度回报器 - 用于在Agent执行过程中发送进度消息
    
    这是一个单例类，确保在整个应用中使用同一个实例
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressReporter, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.max_messages_per_session = 100  # 每个会话最多保留的消息数
    
    def report(self, session_id: str, message: str, stage: str = "processing", 
               metadata: Optional[dict] = None):
        """
        发送进度消息
        
        Args:
            session_id: 会话ID，用于标识特定的Agent执行会话
            message: 进度消息内容
            stage: 执行阶段 (init/analyzing/processing/llm_call/completed/error)
            metadata: 额外的元数据信息
        """
        try:
            progress_data = {
                'session_id': session_id,
                'message': message,
                'stage': stage,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # 添加到存储
            progress_storage[session_id].append(progress_data)
            
            # 限制存储的消息数量
            if len(progress_storage[session_id]) > self.max_messages_per_session:
                progress_storage[session_id] = progress_storage[session_id][-self.max_messages_per_session:]
            
            # 记录日志
            logger.info(f"进度回报 [{session_id}] {stage}: {message}")
            
        except Exception as e:
            logger.error(f"发送进度消息失败: {e}")

# 全局进度回报器实例
progress_reporter = ProgressReporter()

def report_progress(session_id: str, message: str, stage: str = "processing", 
                   metadata: Optional[dict] = None):
    """
    便捷函数：发送进度消息
    
    使用示例：
    ```python
    # 在Agent代码中调用
    from app.api.progress import report_progress
    
    # 任务开始
    report_progress(session_id, "正在分析任务类型...", "analyzing")
    
    # LLM调用
    report_progress(session_id, "正在调用AI模型进行关键词提取...", "llm_call", 
                   {"model": "deepseek", "task": "keyword_extraction"})
    
    # 数据处理
    report_progress(session_id, "正在从知识库检索相关信息...", "processing")
    
    # 任务完成
    report_progress(session_id, "AI回答生成完成", "completed")
    ```
    
    Args:
        session_id: 会话ID
        message: 进度消息
        stage: 执行阶段
        metadata: 额外元数据
    """
    progress_reporter.report(session_id, message, stage, metadata)
    
    # 同时通过WebSocket发送进度消息
    import asyncio
    try:
        # 获取事件循环并发送WebSocket消息
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果在异步上下文中，创建一个任务
            asyncio.create_task(_send_websocket_progress(session_id, message, stage, metadata))
        else:
            # 如果不在异步上下文中，运行新的事件循环
            asyncio.run(_send_websocket_progress(session_id, message, stage, metadata))
    except Exception as e:
        logger.warning(f"WebSocket进度发送失败: {e}")

async def _send_websocket_progress(session_id: str, message: str, stage: str, metadata: Optional[dict] = None):
    """
    内部函数：通过WebSocket发送进度消息
    """
    try:
        from main import send_websocket_progress
        # 将stage映射到progress百分比
        progress_map = {
            "init": 0,
            "analyzing": 20,
            "processing": 50,
            "llm_call": 70,
            "completing": 90,
            "completed": 100,
            "error": 0
        }
        progress = progress_map.get(stage, 50)
        
        await send_websocket_progress(session_id, message, stage, progress, metadata)
    except Exception as e:
        logger.warning(f"WebSocket内部发送失败: {e}")

def abort_session(session_id: str):
    """
    中止指定会话的处理
    
    Args:
        session_id: 要中止的会话ID
    """
    try:
        abort_flags[session_id] = True
        report_progress(session_id, "用户请求中止任务", "error")
        logger.info(f"会话 {session_id} 被用户中止")
    except Exception as e:
        logger.error(f"中止会话失败: {e}")

def is_session_aborted(session_id: str) -> bool:
    """
    检查会话是否被中止
    
    Args:
        session_id: 会话ID
        
    Returns:
        bool: 如果会话被中止返回True，否则返回False
    """
    return abort_flags.get(session_id, False)

def clear_abort_flag(session_id: str):
    """
    清除会话的中止标记
    
    Args:
        session_id: 会话ID
    """
    if session_id in abort_flags:
        del abort_flags[session_id]

async def progress_stream_generator(session_id: str, connection_id: str) -> AsyncGenerator[str, None]:
    """
    生成进度流数据
    
    Args:
        session_id: 会话ID
        connection_id: 连接ID，用于管理多个连接
    """
    try:
        # 注册连接
        active_connections[session_id].add(connection_id)
        
        # 发送连接确认消息
        initial_message = {
            'session_id': session_id,
            'message': '进度监听已启动',
            'stage': 'connected',
            'timestamp': datetime.now().isoformat(),
            'metadata': {'connection_id': connection_id}
        }
        yield f"data: {json.dumps(initial_message, ensure_ascii=False)}\n\n"
        
        # 发送历史消息（如果有）
        if session_id in progress_storage:
            for msg in progress_storage[session_id][-10:]:  # 只发送最近10条
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
        
        # 持续监听新消息
        last_message_count = len(progress_storage[session_id])
        
        while True:
            current_message_count = len(progress_storage[session_id])
            
            # 如果有新消息
            if current_message_count > last_message_count:
                new_messages = progress_storage[session_id][last_message_count:]
                for msg in new_messages:
                    yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                last_message_count = current_message_count
            
            # 检查连接是否仍然活跃
            if connection_id not in active_connections[session_id]:
                break
                
            # 发送心跳
            await asyncio.sleep(1)
            yield f": heartbeat\n\n"
            
    except asyncio.CancelledError:
        # 连接被取消
        pass
    except Exception as e:
        error_message = {
            'session_id': session_id,
            'message': f'进度流错误: {str(e)}',
            'stage': 'error',
            'timestamp': datetime.now().isoformat(),
            'metadata': {'error': str(e)}
        }
        yield f"data: {json.dumps(error_message, ensure_ascii=False)}\n\n"
    finally:
        # 清理连接
        if connection_id in active_connections[session_id]:
            active_connections[session_id].remove(connection_id)
        if not active_connections[session_id]:
            # 如果没有活跃连接，清理该会话的进度数据
            if session_id in progress_storage:
                del progress_storage[session_id]
            if session_id in active_connections:
                del active_connections[session_id]

@router.get("/stream/{session_id}")
async def stream_progress(session_id: str):
    """
    获取指定会话的实时进度流
    
    Args:
        session_id: 会话ID
    
    Returns:
        Server-Sent Events流，包含进度消息
    """
    connection_id = str(uuid.uuid4())
    
    return StreamingResponse(
        progress_stream_generator(session_id, connection_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.post("/send/{session_id}")
async def send_progress(session_id: str, message: str, stage: str = "processing", 
                       metadata: Optional[dict] = None):
    """
    手动发送进度消息（用于测试）
    
    Args:
        session_id: 会话ID
        message: 消息内容
        stage: 执行阶段
        metadata: 额外元数据
    
    Returns:
        发送结果
    """
    try:
        report_progress(session_id, message, stage, metadata)
        return {
            "status": "success",
            "message": "进度消息已发送",
            "session_id": session_id,
            "active_connections": len(active_connections.get(session_id, set()))
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"发送失败: {str(e)}"
        }

@router.get("/status/{session_id}")
async def get_progress_status(session_id: str):
    """
    获取会话的进度状态
    
    Args:
        session_id: 会话ID
    
    Returns:
        会话状态信息
    """
    return {
        "session_id": session_id,
        "total_messages": len(progress_storage.get(session_id, [])),
        "active_connections": len(active_connections.get(session_id, set())),
        "recent_messages": progress_storage.get(session_id, [])[-5:] if session_id in progress_storage else []
    }

@router.delete("/clear/{session_id}")
async def clear_progress(session_id: str):
    """
    清理指定会话的进度数据
    
    Args:
        session_id: 会话ID
    
    Returns:
        清理结果
    """
    try:
        if session_id in progress_storage:
            del progress_storage[session_id]
        if session_id in active_connections:
            active_connections[session_id].clear()
            
        return {
            "status": "success",
            "message": f"会话 {session_id} 的进度数据已清理"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"清理失败: {str(e)}"
        }

@router.post("/abort/{session_id}")
async def abort_session_request(session_id: str):
    """
    中止指定会话的处理
    
    Args:
        session_id: 要中止的会话ID
    
    Returns:
        中止操作的结果
    """
    try:
        abort_session(session_id)
        
        return {
            "status": "success",
            "message": f"已请求中止会话 {session_id}",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"中止会话请求失败: {e}")
        return {
            "status": "error",
            "message": f"中止会话失败: {str(e)}",
            "session_id": session_id
        }