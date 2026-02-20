"""
Credit管理服务 - 处理用户credit查询和扣除
"""

import httpx
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class CreditService:
    """Credit管理服务类"""
    
    def __init__(self):
        self.base_url = "https://rshub.zju.edu.cn/users"
    
    async def check_credits(self, token: str, required_credits: float) -> Tuple[bool, str, Optional[float]]:
        """
        检查用户是否有足够的credit
        
        Args:
            token: 用户token
            required_credits: 需要的credit数量
            
        Returns:
            Tuple[bool, str, Optional[float]]: (是否充足, 消息, 当前余额)
        """
        try:
            # 将float转换为int，因为RSHub API可能期望整数
            credits_to_check = int(required_credits)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/Check-credits",
                    json={"token": token, "credits": credits_to_check},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Credit检查API返回错误状态: {response.status_code}")
                    return False, f"API调用失败: {response.status_code}", None
                
                data = response.json()
                logger.info(f"Credit检查响应: {data}")
                
                # 根据API文档，logic字段表示是否有足够credit
                has_enough = data.get("logic", False)
                message = data.get("message", "")
                
                if has_enough:
                    return True, "余额充足", None
                else:
                    return False, message or "余额不足", None
                    
        except httpx.TimeoutException:
            logger.error("Credit检查超时")
            return False, "网络超时，请稍后重试", None
        except Exception as e:
            logger.error(f"检查credit失败: {str(e)}")
            return False, f"检查余额失败: {str(e)}", None
    
    async def update_credits(self, token: str, credit_change: float) -> Tuple[bool, str, Optional[float]]:
        """
        更新用户credit（正数增加，负数减少）
        
        Args:
            token: 用户token
            credit_change: credit变化量（负数表示扣除）
            
        Returns:
            Tuple[bool, str, Optional[float]]: (是否成功, 消息, 剩余余额)
        """
        try:
            # 将float转换为int，因为RSHub API可能期望整数
            credits_to_update = int(credit_change)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/Update-credits",
                    json={"token": token, "credits": credits_to_update},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Credit更新API返回错误状态: {response.status_code}")
                    return False, f"API调用失败: {response.status_code}", None
                
                data = response.json()
                logger.info(f"Credit更新响应: {data}")
                
                # 根据API文档，result字段表示是否成功
                success = data.get("result", False)
                message = data.get("message", "")
                credits = data.get("credits", None)
                
                if success:
                    return True, "Credit更新成功", credits
                else:
                    return False, message or "Credit更新失败", credits
                    
        except httpx.TimeoutException:
            logger.error("Credit更新超时")
            return False, "网络超时，请稍后重试", None
        except Exception as e:
            logger.error(f"更新credit失败: {str(e)}")
            return False, f"更新余额失败: {str(e)}", None
    
    async def get_remaining_credits(self, token: str) -> Tuple[bool, str, Optional[float]]:
        """
        获取用户剩余credit（通过检查0个credit实现）
        
        Args:
            token: 用户token
            
        Returns:
            Tuple[bool, str, Optional[float]]: (是否成功, 消息, 剩余余额)
        """
        try:
            # 通过检查0个credit来获取当前余额信息
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/Check-credits",
                    json={"token": token, "credits": 0},
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code != 200:
                    logger.error(f"获取余额API返回错误状态: {response.status_code}")
                    return False, f"API调用失败: {response.status_code}", -1
                
                data = response.json()
                logger.info(f"获取余额响应: {data}")
                
                # 从返回消息中尝试提取余额信息
                message = data.get("message", "")
                if message:
                    # 尝试从消息中解析余额数字
                    import re
                    numbers = re.findall(r'\d+', message)
                    if numbers:
                        remaining = float(numbers[-1])  # 取最后一个数字作为余额
                        return True, f"当前余额: {remaining}", remaining
                    else:
                        return True, "余额查询成功，但未能解析出余额数字", -1
                
                return True, "余额查询成功，但未能获取余额信息", -1
                    
        except Exception as e:
            logger.error(f"获取剩余credit失败: {str(e)}")
            return False, f"查询余额失败: {str(e)}", -1

# 全局credit服务实例
credit_service = CreditService()

def get_credit_service() -> CreditService:
    """获取credit服务实例"""
    return credit_service 