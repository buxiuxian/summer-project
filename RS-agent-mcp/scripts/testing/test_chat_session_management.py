"""
会话管理功能测试脚本
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.session import get_chat_session_service
from app.core.config import get_settings

async def test_chat_session_management():
    """测试会话管理功能"""
    
    print("=" * 60)
    print("会话管理功能测试")
    print("=" * 60)
    
    # 获取设置和服务
    settings = get_settings()
    chat_service = get_chat_session_service()
    
    # 使用测试token (在实际环境中应该使用有效的token)
    test_token = settings.RSHUB_TOKEN or "test_token"
    
    if not test_token or test_token == "test_token":
        print("❌ 错误：未找到有效的RSHub token")
        print("请在环境变量或配置文件中设置RSHUB_TOKEN")
        return False
    
    try:
        # 1. 测试会话列表获取
        print("\n1. 测试获取会话列表...")
        sessions = await chat_service.list_sessions(test_token)
        print(f"✅ 成功获取会话列表，共 {len(sessions)} 个会话")
        
        # 2. 测试会话创建
        print("\n2. 测试创建新会话...")
        test_user_prompt = "什么是微波遥感？"
        test_ai_response = "微波遥感是一种利用微波频段的电磁波进行遥感探测的技术。"
        
        create_result = await chat_service.create_session(
            test_token, test_user_prompt, test_ai_response
        )
        
        if create_result.get("success"):
            new_session_id = create_result.get("session_id")
            session_title = create_result.get("title")
            print(f"✅ 成功创建会话: {new_session_id}")
            print(f"   会话标题: {session_title}")
            
            # 3. 测试会话加载
            print("\n3. 测试加载会话...")
            session_data = await chat_service.load_session(test_token, new_session_id)
            if session_data:
                print(f"✅ 成功加载会话")
                print(f"   会话ID: {session_data.get('session_id')}")
                print(f"   标题: {session_data.get('title')}")
                print(f"   消息数量: {len(session_data.get('messages', []))}")
            else:
                print("❌ 加载会话失败")
                return False
            
            # 4. 测试会话更新
            print("\n4. 测试更新会话...")
            update_user_prompt = "微波遥感有什么应用？"
            update_ai_response = "微波遥感在农业监测、环境监测、气象预报等领域有广泛应用。"
            
            update_result = await chat_service.update_session(
                test_token, new_session_id, update_user_prompt, update_ai_response
            )
            
            if update_result.get("success"):
                print("✅ 成功更新会话")
                
                # 验证更新
                updated_session = await chat_service.load_session(test_token, new_session_id)
                if updated_session and len(updated_session.get("messages", [])) == 4:
                    print("✅ 会话更新验证通过")
                else:
                    print("❌ 会话更新验证失败")
                    return False
            else:
                print("❌ 更新会话失败")
                return False
            
            # 5. 测试会话历史获取
            print("\n5. 测试获取会话历史...")
            history = await chat_service.get_session_history(test_token, new_session_id)
            if history and len(history) == 4:
                print(f"✅ 成功获取会话历史，共 {len(history)} 条消息")
                for i, msg in enumerate(history):
                    print(f"   消息 {i+1}: {msg.get('role')} - {msg.get('content')[:50]}...")
            else:
                print("❌ 获取会话历史失败")
                return False
            
            # 6. 测试删除会话
            print("\n6. 测试删除会话...")
            delete_result = await chat_service.delete_session(new_session_id)
            if delete_result.get("success"):
                print("✅ 成功删除会话")
                
                # 验证删除
                deleted_session = await chat_service.load_session(test_token, new_session_id)
                if not deleted_session:
                    print("✅ 会话删除验证通过")
                else:
                    print("❌ 会话删除验证失败")
                    return False
            else:
                print("❌ 删除会话失败")
                return False
            
        else:
            print("❌ 创建会话失败")
            return False
        
        # 7. 测试会话列表刷新
        print("\n7. 测试会话列表刷新...")
        refreshed_sessions = await chat_service.list_sessions(test_token)
        print(f"✅ 刷新后会话列表，共 {len(refreshed_sessions)} 个会话")
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！会话管理功能正常工作。")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_prompt_formatting():
    """测试prompt格式化功能"""
    
    print("\n" + "=" * 60)
    print("Prompt格式化功能测试")
    print("=" * 60)
    
    from app.agent.langchain_prompts import format_chat_history
    
    # 测试数据
    test_messages = [
        {
            "role": "user",
            "content": "什么是微波遥感？",
            "timestamp": "2024-01-01T12:00:00Z"
        },
        {
            "role": "assistant",
            "content": "微波遥感是一种利用微波频段的电磁波进行遥感探测的技术。",
            "timestamp": "2024-01-01T12:01:00Z"
        },
        {
            "role": "user",
            "content": "它有什么应用？",
            "timestamp": "2024-01-01T12:02:00Z"
        },
        {
            "role": "assistant",
            "content": "微波遥感在农业监测、环境监测、气象预报等领域有广泛应用。",
            "timestamp": "2024-01-01T12:03:00Z"
        }
    ]
    
    # 测试格式化
    formatted_history = format_chat_history(test_messages)
    print("✅ 格式化历史对话:")
    print(formatted_history)
    
    # 测试空历史
    empty_history = format_chat_history([])
    print("\n✅ 空历史对话处理:")
    print(empty_history)
    
    print("\n🎉 Prompt格式化功能测试通过！")

async def main():
    """主测试函数"""
    print("开始会话管理系统测试...")
    
    # 测试prompt格式化
    test_prompt_formatting()
    
    # 测试会话管理
    success = await test_chat_session_management()
    
    if success:
        print("\n🎉 所有测试成功完成！")
        return 0
    else:
        print("\n❌ 部分测试失败。")
        return 1

if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 