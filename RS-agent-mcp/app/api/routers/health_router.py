"""
健康检查路由器
处理健康检查和根路径相关的API端点
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "message": "RS Agent MCP服务运行正常"}

@router.get("/")
async def root():
    """根路径端点"""
    return {"message": "欢迎使用RS Agent MCP服务", "version": "0.1.0"}