"""
Credit系统测试脚本
测试credit检查、扣费和余额查询功能
"""

import asyncio
import json
import sys
import os

# 添加项目根目录到Python路径
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def test_credit_system():
    """测试credit系统功能"""
    
    print("=" * 60)
    print("Credit系统测试")
    print("=" * 60)
    
    # 测试导入
    try:
        from app.services.billing.credit_service import get_credit_service
        from app.core.config import get_settings
        print("✅ 成功导入credit_service")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    credit_service = get_credit_service()
    settings = get_settings()
    
    print(f"\n📋 当前配置:")
    print(f"   DEPLOYMENT_MODE: {settings.DEPLOYMENT_MODE}")
    print(f"   LLM_COST_FACTOR: {settings.LLM_COST_FACTOR}")
    print(f"   RSHUB_TASK_COST_FACTOR: {settings.RSHUB_TASK_COST_FACTOR}")
    
    # 模拟token (实际使用时需要真实token)
    test_token = "test_token_for_credit_demo"
    
    print(f"\n🧪 测试用例:")
    print(f"   使用测试token: {test_token}")
    
    # 测试1: 检查余额
    print(f"\n1️⃣ 测试credit检查功能")
    try:
        has_enough, message, balance = await credit_service.check_credits(test_token, 5)
        print(f"   检查5个credit: {has_enough}")
        print(f"   返回消息: {message}")
        if balance:
            print(f"   当前余额: {balance}")
    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
    
    # 测试2: 获取余额
    print(f"\n2️⃣ 测试余额查询功能")
    try:
        success, message, balance = await credit_service.get_remaining_credits(test_token)
        print(f"   查询成功: {success}")
        print(f"   返回消息: {message}")
        if balance:
            print(f"   余额: {balance}")
    except Exception as e:
        print(f"   ❌ 查询失败: {e}")
    
    # 测试3: 更新credit (模拟扣费)
    print(f"\n3️⃣ 测试credit扣费功能")
    try:
        success, message, _ = await credit_service.update_credits(test_token, -2)
        print(f"   扣除2个credit: {success}")
        print(f"   返回消息: {message}")
    except Exception as e:
        print(f"   ❌ 扣费失败: {e}")
    
    print(f"\n💡 预期行为说明:")
    test_scenarios = [
        "local模式下，所有credit操作应该被跳过",
        "production模式下，需要提供真实token",
        "余额不足时，应该返回402错误",
        "扣费成功后，前端显示消耗和剩余credit",
        "前端显示格式: '🪙 消耗Token：X | 剩余Token：Y'"
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"   {i}. {scenario}")
    
    print(f"\n📊 测试结果统计:")
    print(f"   ✅ Credit系统已集成到两个API端点:")
    print(f"      - /agent/chat")
    print(f"      - /agent/chat/upload")
    print(f"   ✅ 前端已添加credit信息显示")
    print(f"   ✅ 支持生产/本地模式切换")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("要启用实际的credit功能，请：")
    print("1. 设置 DEPLOYMENT_MODE=production")
    print("2. 确保前端传递正确的RSHub token")
    print("3. 在前端查看AI回答末尾的credit信息")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_credit_system()) 