"""
通用LLM客户端 - 支持OpenAI、DeepSeek和Ollama三种提供商
"""

import json
import asyncio
import os
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
import logging

import requests
import aiofiles
from .config import settings, get_active_llm_config

logger = logging.getLogger(__name__)

class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """生成回复"""
        pass
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """聊天完成"""
        pass

class DeepSeekClient(BaseLLMClient):
    """DeepSeek客户端（通过火山引擎）"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config["api_key"]
        self.base_url = config["base_url"]
        self.model = config["model"]
        self.temperature = config["temperature"]
        self.timeout = config.get("timeout", 60)
        
        # 设置环境变量（OpenAI库需要）
        os.environ["ARK_API_KEY"] = self.api_key
        
        # 导入OpenAI库
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")
        
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用DeepSeek API生成回复"""
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            return await self.chat_completion(messages, temperature, max_tokens)
            
        except Exception as e:
            logger.error(f"DeepSeek generate请求失败: {str(e)}")
            return f"抱歉，连接到DeepSeek API时出现问题: {str(e)}"
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用DeepSeek API进行对话"""
        try:
            # 在asyncio中运行同步的OpenAI客户端
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens,
                    timeout=self.timeout
                )
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            else:
                logger.error("DeepSeek响应格式异常：没有choices")
                return "抱歉，获取DeepSeek响应时出现问题。"
                
        except Exception as e:
            logger.error(f"DeepSeek chat请求失败: {str(e)}")
            return f"抱歉，连接到DeepSeek API时出现问题: {str(e)}"
    
    async def is_available(self) -> bool:
        """检查DeepSeek API是否可用"""
        try:
            test_response = await self.generate_response(
                "测试连接",
                "你是一个测试助手，请回复'连接成功'"
            )
            return "连接成功" in test_response or len(test_response) > 0
        except Exception:
            return False

class OllamaClient(BaseLLMClient):
    """Ollama客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config["base_url"]
        self.model = config["model"]
        self.temperature = config["temperature"]
        self.timeout = config["timeout"]
        
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用Ollama generate端点生成回复"""
        try:
            # 构建完整的prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # 构建请求数据
            data = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,  # 不使用流式响应
                "options": {
                    "temperature": temperature or self.temperature,
                }
            }
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
            
            # 发送请求
            response = await self._make_request("/api/generate", data)
            
            if response and "response" in response:
                return response["response"]
            else:
                logger.error(f"Ollama响应格式错误: {response}")
                return "抱歉，生成回复时出现问题。"
                
        except Exception as e:
            logger.error(f"Ollama generate请求失败: {str(e)}")
            return f"抱歉，连接到本地LLM时出现问题: {str(e)}"
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用Ollama chat端点进行对话"""
        try:
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature or self.temperature,
                }
            }
            
            if max_tokens:
                data["options"]["num_predict"] = max_tokens
            
            # 发送请求
            response = await self._make_request("/api/chat", data)
            
            if response and "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                logger.error(f"Ollama chat响应格式错误: {response}")
                return "抱歉，聊天时出现问题。"
                
        except Exception as e:
            logger.error(f"Ollama chat请求失败: {str(e)}")
            return f"抱歉，连接到本地LLM时出现问题: {str(e)}"
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送HTTP请求到Ollama"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            # 使用同步requests，但在asyncio中运行
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url, 
                    json=data, 
                    headers=headers, 
                    timeout=self.timeout
                )
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ollama请求失败，状态码: {response.status_code}, 响应: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama HTTP请求异常: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ollama响应JSON解析失败: {str(e)}")
            return None
    
    async def is_available(self) -> bool:
        """检查Ollama服务是否可用"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, timeout=5)
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_models(self) -> List[str]:
        """获取可用模型列表"""
        try:
            response = await self._make_request("/api/tags", {})
            if response and "models" in response:
                return [model["name"] for model in response["models"]]
            return []
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {str(e)}")
            return []

class OpenAIClient(BaseLLMClient):
    """OpenAI客户端"""
    
    def __init__(self, config: Dict[str, Any]):
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.temperature = config["temperature"]
        
        # 导入OpenAI库
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("请安装openai库: pip install openai")
        
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用OpenAI API生成回复"""
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            return await self.chat_completion(messages, temperature, max_tokens)
            
        except Exception as e:
            logger.error(f"OpenAI generate请求失败: {str(e)}")
            return f"抱歉，连接到OpenAI API时出现问题: {str(e)}"
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用OpenAI API进行聊天"""
        try:
            # 在asyncio中运行同步的OpenAI客户端
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature or self.temperature,
                    max_tokens=max_tokens
                )
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or ""
            else:
                logger.error("OpenAI响应格式异常：没有choices")
                return "抱歉，获取OpenAI响应时出现问题。"
                
        except Exception as e:
            logger.error(f"OpenAI chat请求失败: {str(e)}")
            return f"抱歉，连接到OpenAI API时出现问题: {str(e)}"

class LLMClientFactory:
    """LLM客户端工厂"""
    
    @staticmethod
    def create_client() -> BaseLLMClient:
        """根据配置创建LLM客户端"""
        config = get_active_llm_config()
        
        # 所有客户端都使用统一的配置
        # 判断是否是本地服务（如Ollama）
        is_local = "localhost" in config["base_url"] or "127.0.0.1" in config["base_url"]
        
        if is_local and ("ollama" in config["base_url"].lower() or config["base_url"].endswith("11434")):
            return OllamaClient(config)
        else:
            # DeepSeek、OpenAI等都使用同样的客户端
            return DeepSeekClient(config)  # DeepSeekClient实际上是通用的OpenAI兼容客户端
    
    @staticmethod
    async def test_connection() -> tuple[bool, str]:
        """测试LLM连接"""
        try:
            client = LLMClientFactory.create_client()
            config = get_active_llm_config()
            
            if isinstance(client, OllamaClient):
                is_available = await client.is_available()
                if is_available:
                    models = await client.list_models()
                    if config["model"] in models:
                        return True, f"✅ Ollama连接成功，模型 {config['model']} 可用"
                    else:
                        return False, f"❌ 模型 {config['model']} 不可用，可用模型: {models}"
                else:
                    return False, f"❌ 无法连接到Ollama服务 ({config['base_url']})"
            
            else:
                # 测试OpenAI兼容API
                is_available = await client.is_available()
                if is_available:
                    return True, f"✅ API连接成功，模型 {config['model']} 可用"
                else:
                    return False, f"❌ 无法连接到API ({config['base_url']})"
                
        except Exception as e:
            return False, f"❌ LLM连接测试失败: {str(e)}"

# 创建全局客户端实例
_llm_client: Optional[BaseLLMClient] = None

async def get_llm_client() -> BaseLLMClient:
    """获取LLM客户端实例（单例模式）"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClientFactory.create_client()
    return _llm_client

async def quick_generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """快速生成回复的便捷函数"""
    client = await get_llm_client()
    return await client.generate_response(prompt, system_prompt)

async def quick_chat(messages: List[Dict[str, str]]) -> str:
    """快速聊天的便捷函数"""
    client = await get_llm_client()
    return await client.chat_completion(messages) 