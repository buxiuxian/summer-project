"""
日志流API - 提供实时日志推送功能
"""

import asyncio
import json
import logging
import queue
import threading
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

# 创建API路由器
router = APIRouter(prefix="/logs", tags=["logs"])

# 全局日志队列
log_queue = queue.Queue(maxsize=1000)

class LogStreamHandler(logging.Handler):
    """自定义日志处理器，将日志消息推送到队列"""
    
    def __init__(self):
        super().__init__()
        # 过滤掉一些噪音日志
        self.filtered_messages = {
            'HTTP/1.1" 200 OK',  # 普通HTTP请求
            'HTTP/1.1" 304 Not Modified',  # 资源未修改
            'heartbeat',  # 心跳消息
        }
    
    def emit(self, record):
        try:
            # 格式化日志消息
            log_message = self.format(record)
            
            # 过滤掉一些不重要的日志
            if any(filtered in log_message for filtered in self.filtered_messages):
                return
            
            # 确定日志级别
            level_mapping = {
                'DEBUG': 'info',
                'INFO': 'info',
                'WARNING': 'warning',
                'ERROR': 'error',
                'CRITICAL': 'error'
            }
            
            level = level_mapping.get(record.levelname, 'info')
            
            # 创建日志数据
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'message': log_message,
                'logger': record.name
            }
            
            # 添加到队列
            if not log_queue.full():
                log_queue.put(log_data)
            
        except Exception:
            # 避免日志处理器本身出错
            pass

# 创建并配置日志处理器
log_handler = LogStreamHandler()
log_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

# 将处理器仅添加到根日志记录器（避免重复日志）
root_logger = logging.getLogger()
# 检查是否已经添加了处理器，避免重复添加
if log_handler not in root_logger.handlers:
    root_logger.addHandler(log_handler)
    root_logger.setLevel(logging.INFO)  # 确保日志级别正确

# 确保第三方库的日志也能被捕获
important_loggers = [
    'httpx',  # HTTP客户端请求日志
    'openai',  # OpenAI API日志
    'langchain',  # LangChain相关日志
    'uvicorn.access',  # Web服务器访问日志
    'uvicorn.error',  # Web服务器错误日志
]

for logger_name in important_loggers:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    # 确保这些logger的日志会向上传播到根logger
    logger.propagate = True

async def log_stream_generator() -> AsyncGenerator[str, None]:
    """生成日志流数据"""
    last_heartbeat = datetime.now()
    heartbeat_interval = 30  # 30秒发送一次心跳，且不显示在前端
    
    # 发送初始连接消息
    initial_log = {
        'timestamp': datetime.now().isoformat(),
        'level': 'info',
        'message': '日志流服务已启动',
        'logger': 'system'
    }
    sse_data = f"data: {json.dumps(initial_log, ensure_ascii=False)}\n\n"
    yield sse_data
    
    try:
        while True:
            try:
                # 非阻塞地获取日志消息
                log_data = log_queue.get_nowait()
                
                # 格式化为SSE数据
                sse_data = f"data: {json.dumps(log_data, ensure_ascii=False)}\n\n"
                yield sse_data
                
            except queue.Empty:
                # 队列为空时等待
                await asyncio.sleep(1)  # 增加等待时间到1秒
                
                # 检查是否需要发送心跳（不显示在前端）
                now = datetime.now()
                if (now - last_heartbeat).seconds >= heartbeat_interval:
                    # 发送空的心跳包保持SSE连接，但不显示在前端
                    yield ": heartbeat\n\n"
                    last_heartbeat = now
                
            except Exception as e:
                error_log = {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'error',
                    'message': f'日志流错误: {str(e)}',
                    'logger': 'system'
                }
                sse_data = f"data: {json.dumps(error_log, ensure_ascii=False)}\n\n"
                yield sse_data
                await asyncio.sleep(1)
                
    except asyncio.CancelledError:
        # 连接被取消时的清理
        pass
    except Exception as e:
        error_log = {
            'timestamp': datetime.now().isoformat(),
            'level': 'error',
            'message': f'日志流严重错误: {str(e)}',
            'logger': 'system'
        }
        sse_data = f"data: {json.dumps(error_log, ensure_ascii=False)}\n\n"
        yield sse_data

@router.get("/stream")
async def stream_logs():
    """
    获取实时日志流
    
    Returns:
        Server-Sent Events流
    """
    return StreamingResponse(
        log_stream_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

@router.get("/test")
async def test_log():
    """
    测试日志功能
    
    Returns:
        测试结果
    """
    logger = logging.getLogger(__name__)
    
    # 发送测试日志
    logger.info("这是一条测试INFO日志")
    logger.warning("这是一条测试WARNING日志")
    logger.error("这是一条测试ERROR日志")
    
    # 手动添加日志到队列（确保立即可见）
    test_logs = [
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'info',
            'message': '手动测试日志 - INFO级别',
            'logger': 'test'
        },
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'warning',
            'message': '手动测试日志 - WARNING级别',
            'logger': 'test'
        },
        {
            'timestamp': datetime.now().isoformat(),
            'level': 'error',
            'message': '手动测试日志 - ERROR级别',
            'logger': 'test'
        }
    ]
    
    for log_data in test_logs:
        if not log_queue.full():
            log_queue.put(log_data)
    
    return {
        "status": "success", 
        "message": "测试日志已发送",
        "queue_size": log_queue.qsize(),
        "logs_sent": len(test_logs)
    }

@router.get("/clear")
async def clear_logs():
    """
    清除日志队列
    
    Returns:
        清除结果
    """
    try:
        # 清空队列
        while not log_queue.empty():
            try:
                log_queue.get_nowait()
            except queue.Empty:
                break
        
        return {"status": "success", "message": "日志队列已清除"}
        
    except Exception as e:
        return {"status": "error", "message": f"清除日志队列失败: {str(e)}"}

@router.get("/logs/stream")
async def logs_stream(request: Request):
    async def event_generator():
        # 示例：每秒推送一条日志。可替换为实际日志读取逻辑。
        count = 0
        while True:
            await asyncio.sleep(1)
            count += 1
            yield f"data: 日志消息 {count}\n\n"
            if await request.is_disconnected():
                break
    return StreamingResponse(event_generator(), media_type="text/event-stream") 