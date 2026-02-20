#!/usr/bin/env python3
"""
测试LangChain Agent修复后的功能
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.agent.langchain_agent import run_analysis_agent_langchain

async def test_langchain_agent():
    """测试LangChain Agent的各个功能"""
    
    print("=== 测试LangChain Agent修复 ===\n")
    
    # 测试1: 任务分类 (Mode 0)
    print("1. 测试任务分类功能 (Mode 0)")
    try:
        result = await run_analysis_agent_langchain(
            instruction_mode=0,
            user_prompt="什么是微波散射？",
            file_paths=None,
            output_path=None
        )
        print(f"任务分类结果: {result}")
        print("✅ 任务分类功能正常\n")
    except Exception as e:
        print(f"❌ 任务分类功能出错: {str(e)}\n")
    
    # 测试2: 知识问答 (Mode 1)  
    print("2. 测试知识问答功能 (Mode 1)")
    try:
        result = await run_analysis_agent_langchain(
            instruction_mode=1,
            user_prompt="什么是微波遥感？",
            file_paths=None,
            output_path=None
        )
        print(f"知识问答结果: {result[:200]}...")
        print("✅ 知识问答功能正常\n")
    except Exception as e:
        print(f"❌ 知识问答功能出错: {str(e)}\n")
    
    # 测试3: 参数构建环境 (Mode 2)
    print("3. 测试参数构建环境功能 (Mode 2)")
    try:
        result = await run_analysis_agent_langchain(
            instruction_mode=2,
            user_prompt="根据土壤湿度参数构建微波环境",
            file_paths=None,
            output_path=None
        )
        print(f"参数构建环境结果: {result[:200]}...")
        print("✅ 参数构建环境功能正常\n")
    except Exception as e:
        print(f"❌ 参数构建环境功能出错: {str(e)}\n")
    
    # 测试4: 环境推断参数 (Mode 3)
    print("4. 测试环境推断参数功能 (Mode 3)")
    try:
        result = await run_analysis_agent_langchain(
            instruction_mode=3,
            user_prompt="根据微波信号反推土壤参数",
            file_paths=None,
            output_path=None
        )
        print(f"环境推断参数结果: {result[:200]}...")
        print("✅ 环境推断参数功能正常\n")
    except Exception as e:
        print(f"❌ 环境推断参数功能出错: {str(e)}\n")

async def test_langchain_client():
    """测试LangChain客户端"""
    print("=== 测试LangChain客户端 ===\n")
    
    try:
        from app.core.langchain_client import get_langchain_client
        
        client = await get_langchain_client()
        print("✅ LangChain客户端初始化成功")
        
        # 测试基本生成功能
        response = await client.generate_response(
            "你好",
            "你是一个测试助手"
        )
        print(f"基本生成测试: {response[:50]}...")
        print("✅ LangChain客户端基本功能正常\n")
        
    except Exception as e:
        print(f"❌ LangChain客户端测试失败: {str(e)}\n")

async def test_langchain_prompts():
    """测试LangChain提示词模板"""
    print("=== 测试LangChain提示词模板 ===\n")
    
    try:
        from app.agent import langchain_prompts
        
        # 测试任务分类模板
        template = langchain_prompts.TASK_CLASSIFICATION_TEMPLATE
        variables = {
            "user_prompt": "什么是微波散射？",
            "file_info": "无文件上传"
        }
        
        # 测试模板格式化
        messages = template.format_messages(**variables)
        print(f"模板消息数量: {len(messages)}")
        print(f"第一个消息类型: {type(messages[0])}")
        if hasattr(messages[0], 'content'):
            print(f"第一个消息内容: {messages[0].content[:50]}...")
        print("✅ LangChain提示词模板功能正常\n")
        
    except Exception as e:
        print(f"❌ LangChain提示词模板测试失败: {str(e)}\n")

async def main():
    """主函数"""
    print("开始LangChain Agent修复测试...\n")
    
    # 测试LangChain提示词模板
    await test_langchain_prompts()
    
    # 测试LangChain客户端
    await test_langchain_client()
    
    # 测试LangChain Agent
    await test_langchain_agent()
    
    print("=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main()) 