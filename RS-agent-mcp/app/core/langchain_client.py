"""
LangChain客户端 - 使用LangChain框架包装LLM调用
"""

import os
import asyncio
from typing import Dict, List, Any, Optional, Union
import logging

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama

from .config import settings, get_active_llm_config

logger = logging.getLogger(__name__)

class LangChainLLMClient:
    """基于LangChain的LLM客户端"""
    
    def __init__(self):
        """初始化LangChain客户端"""
        self.config = get_active_llm_config()
        self.llm = self._create_llm()
        self.output_parser = StrOutputParser()
        
    def _create_llm(self):
        """根据配置创建相应的LLM实例"""
        # 所有提供商都使用OpenAI兼容接口
        os.environ["OPENAI_API_KEY"] = self.config["api_key"]
        
        # 判断是否是本地服务（如Ollama）
        is_local = "localhost" in self.config["base_url"] or "127.0.0.1" in self.config["base_url"]
        
        if is_local and "ollama" in self.config["base_url"].lower():
            # Ollama使用ChatOllama
            return ChatOllama(
                model=self.config["model"],
                base_url=self.config["base_url"].rstrip("/v1"),  # Ollama不需要/v1后缀
                temperature=self.config["temperature"],
                request_timeout=self.config.get("timeout", 120)
            )
        else:
            # 其他都使用ChatOpenAI
            return ChatOpenAI(
                model=self.config["model"],
                openai_api_base=self.config["base_url"],
                openai_api_key=self.config["api_key"],
                temperature=self.config["temperature"],
                request_timeout=self.config.get("timeout", 120),
                max_tokens=self.config.get("max_tokens", 20000)
            )
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """生成回复"""
        try:
            # 构建消息列表
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            return await self.chat_completion(messages, temperature, max_tokens)
            
        except Exception as e:
            logger.error(f"LangChain generate请求失败: {str(e)}")
            return f"抱歉，生成回复时出现问题: {str(e)}"
    
    async def chat_completion(
        self, 
        messages: Union[List[Dict[str, str]], List],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用LangChain进行对话完成"""
        try:
            # 如果是字典格式的消息，转换为LangChain格式
            if messages and isinstance(messages[0], dict):
                langchain_messages = []
                for msg in messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    
                    if role == "system":
                        langchain_messages.append(SystemMessage(content=content))
                    elif role == "user":
                        langchain_messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        langchain_messages.append(AIMessage(content=content))
                    else:
                        # 默认作为用户消息处理
                        langchain_messages.append(HumanMessage(content=content))
                
                messages = langchain_messages
            
            # 创建临时LLM实例（如果需要自定义参数）
            llm = self.llm
            if temperature is not None or max_tokens is not None:
                llm_kwargs = {}
                if temperature is not None:
                    llm_kwargs["temperature"] = temperature
                if max_tokens is not None:
                    llm_kwargs["max_tokens"] = max_tokens
                
                # 根据LLM类型创建新实例
                if isinstance(self.llm, ChatOpenAI):
                    llm = ChatOpenAI(**{**self.llm.__dict__, **llm_kwargs})
                elif isinstance(self.llm, ChatOllama):
                    llm = ChatOllama(**{**self.llm.__dict__, **llm_kwargs})
            
            # 使用LangChain运行
            chain = llm | self.output_parser
            
            # 在事件循环中运行
            response = await asyncio.to_thread(lambda: chain.invoke(messages))
            
            return response or ""
            
        except Exception as e:
            logger.error(f"LangChain chat请求失败: {str(e)}")
            return f"抱歉，对话完成时出现问题: {str(e)}"
    
    async def invoke_with_template(
        self,
        template: str,
        variables: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """使用模板调用LLM"""
        try:
            # 创建提示模板
            if system_prompt:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", template)
                ])
            else:
                prompt_template = PromptTemplate.from_template(template)
            
            # 创建链
            chain = prompt_template | self.llm | self.output_parser
            
            # 运行链
            response = await asyncio.to_thread(lambda: chain.invoke(variables))
            
            return response or ""
            
        except Exception as e:
            logger.error(f"LangChain模板调用失败: {str(e)}")
            return f"抱歉，模板调用时出现问题: {str(e)}"
    
    async def is_available(self) -> bool:
        """检查LLM是否可用"""
        try:
            test_response = await self.generate_response(
                "测试连接",
                "你是一个测试助手，请回复'连接成功'"
            )
            return "连接成功" in test_response or len(test_response) > 0
        except Exception:
            return False

# 全局LangChain客户端实例
_langchain_client: Optional[LangChainLLMClient] = None

async def get_langchain_client() -> LangChainLLMClient:
    """获取LangChain客户端实例"""
    global _langchain_client
    if _langchain_client is None:
        _langchain_client = LangChainLLMClient()
    return _langchain_client

async def langchain_generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """便捷的LangChain生成函数"""
    client = await get_langchain_client()
    return await client.generate_response(prompt, system_prompt)

async def langchain_chat(messages: List[Dict[str, str]]) -> str:
    """便捷的LangChain对话函数"""
    client = await get_langchain_client()
    return await client.chat_completion(messages)

async def langchain_template(
    template: str,
    variables: Dict[str, Any],
    system_prompt: Optional[str] = None
) -> str:
    """便捷的LangChain模板函数"""
    client = await get_langchain_client()
    return await client.invoke_with_template(template, variables, system_prompt) 