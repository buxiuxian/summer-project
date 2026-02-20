"""
配置管理 - 集中管理应用配置和环境变量
"""

import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用设置类"""
    
    # LLM配置 - OpenAI兼容API
    BASE_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    API_KEY: str = ""
    MODEL: str = "deepseek-r1-250528"
    
    # 可选的LLM参数
    LLM_TEMPERATURE: float = 0.7
    LLM_TIMEOUT: int = 120
    LLM_MAX_TOKENS: int = 20000
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    RELOAD: bool = True
    
    # 应用信息
    APP_NAME: str = "RS Agent MCP"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "微波遥感智能分析代理服务"
    
    # 文件存储配置
    MAX_FILE_SIZE: int = 20 * 1024 * 1024  # 20MB
    ALLOWED_FILE_TYPES: list = [".txt", ".csv", ".json", ".xml", ".dat", ".log"]
    SESSION_CLEANUP_HOURS: int = 24
    
    # 知识库配置
    KNOWLEDGE_BASE_PATH: str = "file_storage"
    VECTOR_DB_PATH: str = "faiss_index_domain_science"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    EMBEDDING_PATH: str = ""  # 嵌入模型缓存路径，为空时使用默认HuggingFace缓存
    MAX_RETRIEVAL_DOCS: int = 3
    
    # RAG配置
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    SIMILARITY_THRESHOLD: float = 0.7
    
    # Agent配置
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    MAX_TOKENS: int = 2000
    
    # RSHub配置
    RSHUB_TOKEN: str = ""
    
    # 环境模式配置
    DEPLOYMENT_MODE: Literal["production", "local"] = "local"  # production: 从RSHub主站获取token, local: 使用配置文件token
    
    # 会话存储配置
    ENABLE_LOCAL_SESSION_CACHE: bool = True  # 是否启用本地会话缓存（production模式下建议设为False，使用RSHub作为主要存储）
    
    # 计费配置
    LLM_COST_FACTOR: float = 1.0  # LLM调用定价系数
    RSHUB_TASK_COST_FACTOR: float = 1.0  # RSHub任务提交定价系数
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._validate_config()
    
    def _validate_config(self):
        """验证配置的有效性"""
        if not self.API_KEY and not self.DEBUG:
            raise ValueError("生产环境下必须设置 API_KEY")
        
        if self.MAX_FILE_SIZE <= 0:
            raise ValueError("MAX_FILE_SIZE 必须大于 0")
        
        if self.PORT < 1 or self.PORT > 65535:
            raise ValueError("PORT 必须在 1-65535 范围内")

# 创建全局设置实例
settings = Settings()

def get_settings() -> Settings:
    """获取设置实例"""
    return settings

def update_settings(**kwargs) -> Settings:
    """更新设置（主要用于测试）"""
    global settings
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
        else:
            raise ValueError(f"未知的配置项: {key}")
    return settings

# 配置验证函数
def validate_api_key() -> bool:
    """验证API密钥是否有效"""
    api_key = settings.API_KEY
    if not api_key:
        return False
    
    # 简单验证API密钥长度
    if len(api_key) < 10:
        return False
    
    return True

def get_active_llm_config() -> dict:
    """获取当前激活的LLM配置"""
    return {
        "provider": "openai",  # 所有提供商都使用OpenAI兼容接口
        "api_key": settings.API_KEY,
        "base_url": settings.BASE_URL,
        "model": settings.MODEL,
        "temperature": settings.LLM_TEMPERATURE,
        "timeout": settings.LLM_TIMEOUT,
        "max_tokens": settings.LLM_MAX_TOKENS,
    }

def get_database_url() -> str:
    """获取数据库连接URL（如果需要的话）"""
    # 暂时不需要数据库，返回空字符串
    return ""

def get_cors_origins() -> list:
    """获取CORS允许的源"""
    if settings.DEBUG:
        return ["*"]  # 开发环境允许所有源
    else:
        # 生产环境应该指定具体的域名
        return [
            "http://localhost:3000",
            "http://localhost:8080",
            "https://your-domain.com"
        ]

def get_middleware_config() -> dict:
    """获取中间件配置"""
    return {
        "cors": {
            "allow_origins": get_cors_origins(),
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        },
        "gzip": {
            "minimum_size": 1000,
        }
    }

# 环境检查函数
def is_development() -> bool:
    """检查是否为开发环境"""
    return settings.DEBUG

def is_production() -> bool:
    """检查是否为生产环境"""
    return not settings.DEBUG

def get_log_config() -> dict:
    """获取日志配置"""
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": settings.LOG_FORMAT,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": settings.LOG_LEVEL,
            "handlers": ["default"],
        },
    }

# 打印配置信息（仅在调试模式下）
if settings.DEBUG:
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📡 服务器将在 {settings.HOST}:{settings.PORT} 启动")
    print(f"🤖 LLM配置:")
    print(f"  🔗 API地址: {settings.BASE_URL}")
    print(f"  🔑 API密钥状态: {'✅ 已配置' if settings.API_KEY else '❌ 未配置'}")
    print(f"  🧠 模型: {settings.MODEL}")
    print(f"  🌡️ 温度: {settings.LLM_TEMPERATURE}")
    print(f"  ⏱️ 超时: {settings.LLM_TIMEOUT}秒")
    print(f"  📝 最大令牌: {settings.LLM_MAX_TOKENS}")
    print(f"📂 知识库路径: {settings.KNOWLEDGE_BASE_PATH}")
    print(f"🔧 调试模式: {'开启' if settings.DEBUG else '关闭'}")
else:
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} (生产模式)") 