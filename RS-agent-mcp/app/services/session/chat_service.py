"""
会话服务 - 管理用户会话文件
"""

import json
import requests
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from ...core.config import get_settings

logger = logging.getLogger(__name__)

class ChatSessionService:
    """会话服务类"""
    
    def __init__(self):
        self.settings = get_settings()
        self.rshub_api_base = "https://rshub.zju.edu.cn/users/api"
        
        # 根据配置决定是否启用本地缓存
        self.enable_local_cache = getattr(self.settings, 'ENABLE_LOCAL_SESSION_CACHE', True)
        
        # 本地会话缓存目录（仅在启用时创建）
        if self.enable_local_cache:
            self.local_cache_dir = Path("session_cache")
            self.local_cache_dir.mkdir(exist_ok=True)
        else:
            self.local_cache_dir = None
        
        # 会话管理配置
        self.max_history_messages = 50  # 单个会话最大历史消息数（超过会截断）
        self.max_session_age_days = 30  # 会话最大保留天数（超过会自动清理）
        self.max_total_sessions = 100  # 最大会话总数（超过会删除最旧的）
        
        logger.info(f"会话服务初始化，部署模式: {self.settings.DEPLOYMENT_MODE}")
        logger.info(f"本地缓存: {'启用' if self.enable_local_cache else '禁用'}")
        if self.enable_local_cache:
            logger.info(f"本地缓存目录: {self.local_cache_dir}")
        logger.info(f"会话配置: 最大历史={self.max_history_messages}条, 保留={self.max_session_age_days}天, 最大会话数={self.max_total_sessions}")
    
    async def create_session(self, token: str, user_prompt: str, ai_response: str) -> Dict[str, Any]:
        """
        创建新的会话
        
        Args:
            token: 用户token
            user_prompt: 用户的第一条消息
            ai_response: AI的回复
            
        Returns:
            包含session_id和title的字典
        """
        try:
            # 生成会话ID (时间戳精确到毫秒)
            session_id = str(int(datetime.now().timestamp() * 1000))
            
            # 生成会话标题
            title = await self._generate_session_title(user_prompt, ai_response)
            
            # 创建会话数据
            session_data = {
                "session_id": session_id,
                "title": title,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": [
                    {
                        "role": "user",
                        "content": user_prompt,
                        "timestamp": datetime.now().isoformat()
                    },
                    {
                        "role": "assistant",
                        "content": ai_response,
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            # 先保存到本地缓存（确保即使RSHub失败也能保存）
            local_success = await self._save_session_to_local(session_id, session_data)
            
            # 尝试保存到RSHub（失败不影响本地保存）
            rshub_success = await self._save_session_to_rshub(token, session_id, session_data)
            
            if local_success:
                logger.info(f"会话 {session_id} 已保存到本地缓存")
                if rshub_success:
                    logger.info(f"会话 {session_id} 已同步到RSHub")
                else:
                    logger.warning(f"会话 {session_id} 本地保存成功，但RSHub同步失败（已使用本地缓存）")
                
                return {
                    "session_id": session_id,
                    "title": title,
                    "success": True,
                    "local_cache": True,
                    "rshub_sync": rshub_success
                }
            else:
                logger.error(f"会话 {session_id} 保存失败（本地和RSHub都失败）")
                return {
                    "session_id": session_id,
                    "title": title,
                    "success": False,
                    "error": "保存会话失败"
                }
                
        except Exception as e:
            logger.error(f"创建会话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_session(self, token: str, session_id: str, user_prompt: str, ai_response: str) -> Dict[str, Any]:
        """
        更新现有会话
        
        Args:
            token: 用户token
            session_id: 会话ID
            user_prompt: 用户的新消息
            ai_response: AI的回复
            
        Returns:
            更新结果
        """
        try:
            # 优先从本地缓存加载，如果本地没有再从RSHub加载（与load_session逻辑一致）
            session_data = await self.load_session(token, session_id)
            
            if not session_data:
                logger.warning(f"会话 {session_id} 在本地和RSHub都不存在，将创建新会话")
                # 如果会话不存在，创建一个新的会话结构
                session_data = {
                    "session_id": session_id,
                    "title": user_prompt[:50] if len(user_prompt) > 50 else user_prompt,
                    "messages": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            
            # 添加新消息
            session_data["messages"].append({
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat()
            })
            
            session_data["messages"].append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # 限制历史消息数量，只保留最近的N条（防止内存爆炸）
            if len(session_data["messages"]) > self.max_history_messages:
                # 保留前2条（初始对话）和最后N-2条
                kept_messages = session_data["messages"][:2]  # 保留初始对话
                kept_messages.extend(session_data["messages"][-(self.max_history_messages-2):])
                session_data["messages"] = kept_messages
                logger.info(f"会话 {session_id} 历史消息超过限制，已截断为 {len(kept_messages)} 条")
            
            # 更新时间戳
            session_data["updated_at"] = datetime.now().isoformat()
            
            # 生产模式：优先保存到RSHub（确保数据持久化）
            # 本地模式：先保存到本地缓存，再尝试同步到RSHub
            if self.settings.DEPLOYMENT_MODE == "production":
                # 生产模式：RSHub是主要存储
                rshub_success = await self._save_session_to_rshub(token, session_id, session_data)
                if rshub_success:
                    logger.info(f"会话 {session_id} 已保存到RSHub")
                    # 如果启用了本地缓存，也保存到本地缓存作为加速层
                    if self.enable_local_cache:
                        await self._save_session_to_local(session_id, session_data)
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "local_cache": self.enable_local_cache,
                        "rshub_sync": True
                    }
                else:
                    # RSHub保存失败，尝试保存到本地缓存作为fallback
                    if self.enable_local_cache:
                        local_success = await self._save_session_to_local(session_id, session_data)
                        if local_success:
                            logger.warning(f"会话 {session_id} RSHub保存失败，已保存到本地缓存（可能数据不同步）")
                            return {
                                "success": True,
                                "session_id": session_id,
                                "local_cache": True,
                                "rshub_sync": False
                            }
                    
                    logger.error(f"会话 {session_id} 保存失败（RSHub和本地缓存都失败）")
                    return {
                        "success": False,
                        "error": "更新会话失败"
                    }
            else:
                # 本地模式：先保存到本地缓存，再尝试同步到RSHub
                local_success = await self._save_session_to_local(session_id, session_data) if self.enable_local_cache else False
                rshub_success = await self._save_session_to_rshub(token, session_id, session_data)
                
                if local_success or rshub_success:
                    if local_success:
                        logger.info(f"会话 {session_id} 已更新到本地缓存")
                    if rshub_success:
                        logger.info(f"会话 {session_id} 已同步到RSHub")
                    elif local_success:
                        logger.warning(f"会话 {session_id} 本地更新成功，但RSHub同步失败（已使用本地缓存）")
                    
                    return {
                        "success": True,
                        "session_id": session_id,
                        "local_cache": local_success,
                        "rshub_sync": rshub_success
                    }
                else:
                    logger.error(f"会话 {session_id} 更新失败（本地和RSHub都失败）")
                    return {
                        "success": False,
                        "error": "更新会话失败"
                    }
                
        except Exception as e:
            logger.error(f"更新会话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def load_session(self, token: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        加载会话数据
        - 生产模式：优先从RSHub加载（本地缓存仅作为可选的加速层）
        - 本地模式：优先从本地缓存加载，如果本地没有再从RSHub加载
        
        Args:
            token: 用户token
            session_id: 会话ID
            
        Returns:
            会话数据或None
        """
        try:
            # 生产模式：优先从RSHub加载（确保数据一致性）
            if self.settings.DEPLOYMENT_MODE == "production":
                rshub_data = await self._load_session_from_rshub(token, session_id)
                if rshub_data:
                    logger.info(f"从RSHub加载会话 {session_id}")
                    # 如果启用了本地缓存，也保存到本地缓存作为加速层
                    if self.enable_local_cache:
                        await self._save_session_to_local(session_id, rshub_data)
                    return rshub_data
                
                # RSHub没有，尝试从本地缓存加载（作为fallback）
                if self.enable_local_cache:
                    local_data = await self._load_session_from_local(session_id)
                    if local_data:
                        logger.warning(f"RSHub未找到会话 {session_id}，从本地缓存加载（可能数据不同步）")
                        return local_data
                
                logger.warning(f"会话 {session_id} 在RSHub和本地缓存都不存在")
                return None
            
            # 本地模式：优先从本地缓存加载（提高性能）
            else:
                if self.enable_local_cache:
                    local_data = await self._load_session_from_local(session_id)
                    if local_data:
                        logger.info(f"从本地缓存加载会话 {session_id}")
                        return local_data
                
                # 如果本地没有，从RSHub加载
                rshub_data = await self._load_session_from_rshub(token, session_id)
                if rshub_data:
                    logger.info(f"从RSHub加载会话 {session_id}")
                    # 保存到本地缓存以便下次快速访问
                    if self.enable_local_cache:
                        await self._save_session_to_local(session_id, rshub_data)
                    return rshub_data
                
                logger.warning(f"会话 {session_id} 在本地和RSHub都不存在")
                return None
        except Exception as e:
            logger.error(f"加载会话失败: {str(e)}")
            return None
    
    async def find_latest_session(self, token: str) -> Optional[Dict[str, Any]]:
        """
        查找最近的会话（当没有提供chat_id时使用）
        
        Args:
            token: 用户token
            
        Returns:
            最近的会话数据或None
        """
        try:
            # 从本地缓存查找最近的会话
            local_sessions = await self._list_local_sessions()
            if local_sessions:
                # 按更新时间排序，返回最新的
                local_sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
                latest_session_id = local_sessions[0]["session_id"]
                logger.info(f"找到最近的本地会话: {latest_session_id}")
                return await self.load_session(token, latest_session_id)
            
            # 如果本地没有，从RSHub查找
            rshub_session_ids = await self._get_session_ids_from_rshub(token)
            if rshub_session_ids:
                # 返回第一个（通常是最新的）
                latest_session_id = rshub_session_ids[0]
                logger.info(f"找到最近的RSHub会话: {latest_session_id}")
                return await self.load_session(token, latest_session_id)
            
            logger.info("未找到任何会话")
            return None
        except Exception as e:
            logger.error(f"查找最近会话失败: {str(e)}")
            return None
    
    async def list_sessions(self, token: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有会话列表
        合并本地缓存和RSHub的会话列表
        
        Args:
            token: 用户token
            
        Returns:
            会话列表
        """
        try:
            sessions = []
            session_ids_set = set()
            
            # 先从本地缓存获取会话列表
            local_sessions = await self._list_local_sessions()
            for session_data in local_sessions:
                session_id = session_data.get("session_id")
                if session_id:
                    session_ids_set.add(session_id)
                    sessions.append(session_data)
            
            # 从RSHub获取会话ID列表
            rshub_session_ids = await self._get_session_ids_from_rshub(token)
            
            # 添加RSHub中但本地没有的会话
            for session_id in rshub_session_ids:
                if session_id not in session_ids_set:
                    session_data = await self._load_session_from_rshub(token, session_id)
                    if session_data:
                        session_ids_set.add(session_id)
                        sessions.append({
                            "session_id": session_id,
                            "title": session_data.get("title", "未命名会话"),
                            "created_at": session_data.get("created_at"),
                            "updated_at": session_data.get("updated_at"),
                            "message_count": len(session_data.get("messages", []))
                        })
            
            # 按更新时间排序
            sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            
            return sessions
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {str(e)}")
            return []
    
    async def _list_local_sessions(self) -> List[Dict[str, Any]]:
        """
        列出本地缓存的所有会话
        
        Returns:
            会话列表
        """
        # 如果本地缓存未启用，返回空列表
        if not self.enable_local_cache or self.local_cache_dir is None:
            return []
        
        sessions = []
        try:
            for session_file in self.local_cache_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        sessions.append({
                            "session_id": session_data.get("session_id", session_file.stem),
                            "title": session_data.get("title", "未命名会话"),
                            "created_at": session_data.get("created_at"),
                            "updated_at": session_data.get("updated_at"),
                            "message_count": len(session_data.get("messages", []))
                        })
                except Exception as e:
                    logger.warning(f"读取本地会话文件失败 {session_file}: {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"列出本地会话失败: {str(e)}")
        
        return sessions
    
    async def _cleanup_old_sessions(self):
        """
        清理旧会话
        - 删除超过最大保留天数的会话
        - 如果会话总数超过限制，删除最旧的会话
        """
        # 如果本地缓存未启用，直接返回
        if not self.enable_local_cache or self.local_cache_dir is None:
            return
        
        try:
            import time
            from datetime import datetime, timedelta
            
            # 计算过期时间戳
            expire_time = datetime.now() - timedelta(days=self.max_session_age_days)
            
            sessions_to_check = []
            expired_sessions = []
            
            # 扫描所有会话文件
            for session_file in self.local_cache_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        updated_at_str = session_data.get("updated_at", "")
                        
                        if updated_at_str:
                            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
                            if updated_at.tzinfo:
                                updated_at = updated_at.replace(tzinfo=None)
                            
                            # 检查是否过期
                            if updated_at < expire_time:
                                expired_sessions.append(session_file)
                            else:
                                sessions_to_check.append((session_file, updated_at))
                except Exception as e:
                    logger.warning(f"检查会话文件失败 {session_file}: {str(e)}")
                    # 如果文件损坏，也标记为删除
                    expired_sessions.append(session_file)
            
            # 删除过期会话
            for session_file in expired_sessions:
                try:
                    session_file.unlink()
                    logger.info(f"已删除过期会话: {session_file.name}")
                except Exception as e:
                    logger.warning(f"删除过期会话失败 {session_file}: {str(e)}")
            
            # 如果会话总数仍然超过限制，删除最旧的会话
            if len(sessions_to_check) > self.max_total_sessions:
                # 按更新时间排序，删除最旧的
                sessions_to_check.sort(key=lambda x: x[1])
                sessions_to_delete = sessions_to_check[:len(sessions_to_check) - self.max_total_sessions]
                
                for session_file, _ in sessions_to_delete:
                    try:
                        session_file.unlink()
                        logger.info(f"已删除旧会话（超过总数限制）: {session_file.name}")
                    except Exception as e:
                        logger.warning(f"删除旧会话失败 {session_file}: {str(e)}")
            
            if expired_sessions or (len(sessions_to_check) > self.max_total_sessions):
                logger.info(f"会话清理完成: 删除过期={len(expired_sessions)}个, 当前会话数={len(sessions_to_check)}")
                
        except Exception as e:
            logger.error(f"清理旧会话失败: {str(e)}")
    
    async def cleanup_old_sessions_manual(self) -> Dict[str, Any]:
        """
        手动触发清理旧会话（可用于API端点）
        
        Returns:
            清理结果统计
        """
        # 如果本地缓存未启用，返回提示
        if not self.enable_local_cache or self.local_cache_dir is None:
            return {
                "success": True,
                "message": "本地缓存未启用，无需清理",
                "deleted_count": 0,
                "remaining_count": 0
            }
        
        try:
            before_count = len(list(self.local_cache_dir.glob("*.json")))
            await self._cleanup_old_sessions()
            after_count = len(list(self.local_cache_dir.glob("*.json")))
            
            return {
                "success": True,
                "deleted_count": before_count - after_count,
                "remaining_count": after_count
            }
        except Exception as e:
            logger.error(f"手动清理会话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            删除结果
        """
        try:
            # 调用RSHub API删除会话
            response = requests.post(
                f"{self.rshub_api_base}/delete-chat",
                json={"chatid": session_id},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("result"):
                    logger.info(f"会话 {session_id} 删除成功")
                    return {
                        "success": True,
                        "session_id": session_id
                    }
                else:
                    logger.error(f"会话 {session_id} 删除失败: {result.get('error_message')}")
                    return {
                        "success": False,
                        "error": result.get("error_message", "删除失败")
                    }
            else:
                logger.error(f"删除会话API调用失败: {response.status_code}")
                return {
                    "success": False,
                    "error": f"API调用失败: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"删除会话失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_session_history(self, token: str, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话历史消息
        优先从本地缓存加载
        
        Args:
            token: 用户token
            session_id: 会话ID
            
        Returns:
            消息列表
        """
        try:
            session_data = await self.load_session(token, session_id)
            if session_data:
                return session_data.get("messages", [])
            return []
        except Exception as e:
            logger.error(f"获取会话历史失败: {str(e)}")
            return []
    
    async def _generate_session_title(self, user_prompt: str, ai_response: str) -> str:
        """
        生成会话标题
        
        Args:
            user_prompt: 用户问题
            ai_response: AI回复
            
        Returns:
            会话标题
        """
        try:
            # 使用LLM生成标题
            from ...core.llm_client import get_llm_client
            client = await get_llm_client()
            
            title_prompt = f"""请根据以下用户问题和AI回答生成一个简短的会话标题（10个字以内）：

用户问题：{user_prompt}
AI回答：{ai_response[:200]}...

请直接输出标题，不要包含其他内容。"""
            
            title = await client.generate_response(
                title_prompt,
                "你是一个会话标题生成专家，擅长用简洁的语言概括对话主题。"
            )
            
            # 清理标题
            title = title.strip().replace("\n", " ").replace('"', '').replace("'", '')
            
            # 限制长度
            if len(title) > 20:
                title = title[:20] + "..."
            
            if not title:
                title = "新对话"
            
            return title
            
        except Exception as e:
            logger.error(f"生成会话标题失败: {str(e)}")
            # 从用户问题中提取关键词作为标题
            words = user_prompt.split()
            if len(words) > 3:
                return " ".join(words[:3]) + "..."
            return user_prompt[:20] + "..." if len(user_prompt) > 20 else user_prompt
    
    async def _save_session_to_local(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        保存会话到本地缓存
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            
        Returns:
            是否保存成功
        """
        # 如果本地缓存未启用，直接返回False
        if not self.enable_local_cache or self.local_cache_dir is None:
            return False
        
        try:
            # 构建文件路径
            session_file = self.local_cache_dir / f"{session_id}.json"
            
            # 保存到本地文件
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"会话 {session_id} 已保存到本地: {session_file}")
            
            # 定期清理旧会话（每次保存时触发，避免频繁清理）
            await self._cleanup_old_sessions()
            
            return True
            
        except Exception as e:
            logger.error(f"保存会话到本地缓存失败: {str(e)}")
            return False
    
    async def _load_session_from_local(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        从本地缓存加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据或None
        """
        # 如果本地缓存未启用，直接返回None
        if not self.enable_local_cache or self.local_cache_dir is None:
            return None
        
        try:
            session_file = self.local_cache_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            logger.debug(f"从本地缓存加载会话 {session_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"从本地缓存加载会话失败: {str(e)}")
            return None
    
    async def _save_session_to_rshub(self, token: str, session_id: str, session_data: Dict[str, Any]) -> bool:
        """
        保存会话到RSHub
        
        Args:
            token: 用户token
            session_id: 会话ID
            session_data: 会话数据
            
        Returns:
            是否保存成功
        """
        try:
            # 准备文件数据
            json_data = json.dumps(session_data, ensure_ascii=False, indent=2)
            
            # 调用RSHub API
            files = {
                'file': ('session.json', json_data, 'application/json')
            }
            
            data = {
                'token': token,
                'chatid': session_id
            }
            
            response = requests.post(
                f"{self.rshub_api_base}/create-update-chat",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    # 检查响应内容类型
                    content_type = response.headers.get('content-type', '')
                    if 'application/json' not in content_type:
                        # RSHub可能返回空响应或非JSON响应
                        response_text = response.text.strip()
                        if not response_text:
                            # 空响应通常表示成功
                            logger.info(f"RSHub返回空响应，视为成功")
                            return True
                        elif 'success' in response_text.lower() or 'ok' in response_text.lower():
                            logger.info(f"RSHub返回成功消息: {response_text[:100]}")
                            return True
                        else:
                            logger.warning(f"RSHub返回非JSON响应: {response_text[:200]}")
                            return False
                    
                    result = response.json()
                    return result.get("result", False)
                except json.JSONDecodeError as e:
                    # JSON解析失败，但可能是成功响应（空响应）
                    response_text = response.text.strip()
                    if not response_text:
                        logger.info(f"RSHub返回空响应（JSON解析失败但视为成功）")
                        return True
                    logger.warning(f"RSHub响应JSON解析失败: {str(e)}, 响应内容: {response_text[:200]}")
                    return False
            else:
                logger.error(f"保存会话API调用失败: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"保存会话到RSHub失败: {str(e)}")
            return False
    
    async def _load_session_from_rshub(self, token: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        从RSHub加载会话
        
        Args:
            token: 用户token
            session_id: 会话ID
            
        Returns:
            会话数据或None
        """
        try:
            response = requests.post(
                f"{self.rshub_api_base}/retrieve-chat",
                json={
                    "token": token,
                    "chatid": session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    # 返回的是JSON文件内容
                    return response.json()
                except json.JSONDecodeError:
                    # RSHub可能返回空响应或非JSON响应
                    response_text = response.text.strip()
                    if not response_text:
                        logger.warning(f"RSHub返回空响应（会话可能不存在）")
                    else:
                        logger.warning(f"RSHub返回非JSON响应: {response_text[:200]}")
                    return None
            else:
                logger.warning(f"加载会话API调用失败: {response.status_code}，将使用本地缓存")
                return None
                
        except json.JSONDecodeError as e:
            # RSHub可能返回空响应或非JSON响应，这是正常的（有本地缓存作为fallback）
            logger.warning(f"从RSHub加载会话失败（JSON解析错误）: {str(e)}，将使用本地缓存")
            return None
        except Exception as e:
            # 网络错误或其他异常，使用warning级别（有本地缓存作为fallback）
            logger.warning(f"从RSHub加载会话失败: {str(e)}，将使用本地缓存")
            return None
    
    async def _get_session_ids_from_rshub(self, token: str) -> List[str]:
        """
        从RSHub获取会话ID列表
        
        Args:
            token: 用户token
            
        Returns:
            会话ID列表
        """
        try:
            response = requests.post(
                f"{self.rshub_api_base}/list-chats",
                json={"token": token},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("chatids", [])
            else:
                logger.error(f"获取会话列表API调用失败: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"从RSHub获取会话ID列表失败: {str(e)}")
            return []

# 全局会话服务实例
_chat_session_service = None

def get_chat_session_service() -> ChatSessionService:
    """获取会话服务实例"""
    global _chat_session_service
    if _chat_session_service is None:
        _chat_session_service = ChatSessionService()
    return _chat_session_service 