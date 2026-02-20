"""
认证服务 - 处理RSHub token认证
"""

from typing import Optional
import logging
from ...core.config import get_settings

logger = logging.getLogger(__name__)

class AuthService:
    """认证服务类"""
    
    @staticmethod
    def get_rshub_token(request_token: Optional[str] = None) -> str:
        """
        获取RSHub token
        
        Args:
            request_token: 请求中携带的token
            
        Returns:
            有效的RSHub token
            
        Raises:
            ValueError: 如果无法获取有效token
        """
        settings = get_settings()
        
        # 根据部署模式决定使用哪个token
        if settings.DEPLOYMENT_MODE == "production":
            # 生产环境：必须使用请求中的token
            if not request_token:
                raise ValueError("生产环境下必须提供RSHub token")
            
            # 验证token格式（简单验证）
            if len(request_token) < 10:
                raise ValueError("无效的RSHub token格式")
            
            logger.info("使用请求中提供的RSHub token")
            return request_token
            
        else:  # local模式
            # 本地模式：优先使用配置文件中的token
            if settings.RSHUB_TOKEN:
                logger.info("使用配置文件中的RSHub token")
                return settings.RSHUB_TOKEN
            
            # 如果配置文件没有token，尝试使用请求中的token
            if request_token:
                logger.info("配置文件未设置token，使用请求中提供的token")
                return request_token
            
            # 都没有token，抛出错误
            raise ValueError("未找到有效的RSHub token，请在配置文件中设置或在请求中提供")
    
    @staticmethod
    def validate_token(token: str) -> bool:
        """
        验证token有效性
        
        Args:
            token: 要验证的token
            
        Returns:
            是否有效
        """
        # 基本格式验证
        if not token or len(token) < 10:
            return False
        
        # TODO: 未来可以添加更多验证逻辑，如：
        # - 调用RSHub API验证token
        # - 检查token过期时间
        # - 验证token权限范围
        
        return True

# 全局认证服务实例
auth_service = AuthService()

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return auth_service 