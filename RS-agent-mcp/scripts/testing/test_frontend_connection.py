#!/usr/bin/env python3
"""
前后端连接诊断工具
用于测试RS Agent MCP与RSHub前端的连接问题
"""

import requests
import json
import time
import asyncio
import websockets
from typing import Dict, Any

class ConnectionDiagnostic:
    """连接诊断工具类"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace('http', 'ws')
        
    def test_server_basic(self) -> Dict[str, Any]:
        """测试服务器基本连通性"""
        print("🔍 1. 测试服务器基本连通性...")
        results = {}
        
        # 测试健康检查
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            results['health'] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text
            }
            print(f"   ✅ 健康检查: {response.status_code}")
        except Exception as e:
            results['health'] = {'success': False, 'error': str(e)}
            print(f"   ❌ 健康检查失败: {e}")
        
        # 测试根路径
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            results['root'] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text
            }
            print(f"   ✅ 根路径: {response.status_code}")
        except Exception as e:
            results['root'] = {'success': False, 'error': str(e)}
            print(f"   ❌ 根路径失败: {e}")
            
        return results
    
    def test_cors_headers(self) -> Dict[str, Any]:
        """测试CORS配置"""
        print("\n🔍 2. 测试CORS配置...")
        results = {}
        
        try:
            # 发送OPTIONS预检请求
            headers = {
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            response = requests.options(f"{self.base_url}/agent/chat", headers=headers, timeout=5)
            
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            results['options'] = {
                'status_code': response.status_code,
                'success': response.status_code in [200, 204],
                'cors_headers': cors_headers
            }
            
            print(f"   ✅ OPTIONS请求: {response.status_code}")
            print(f"   📋 CORS Headers: {cors_headers}")
            
        except Exception as e:
            results['options'] = {'success': False, 'error': str(e)}
            print(f"   ❌ OPTIONS请求失败: {e}")
            
        return results
    
    def test_agent_endpoints(self) -> Dict[str, Any]:
        """测试Agent API端点"""
        print("\n🔍 3. 测试Agent API端点...")
        results = {}
        
        # 测试聊天端点
        try:
            data = {
                "message": "测试连接",
                "session_id": "test_session_123",
                "token": "test_token",
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/agent/chat",
                headers={
                    'Content-Type': 'application/json',
                    'Origin': 'http://localhost:3000'
                },
                json=data,
                timeout=10
            )
            
            results['chat'] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'response': response.json() if response.status_code == 200 else response.text
            }
            
            if response.status_code == 200:
                print(f"   ✅ 聊天端点: {response.status_code}")
                print(f"   📝 响应预览: {response.json().get('response', '')[:100]}...")
            else:
                print(f"   ❌ 聊天端点失败: {response.status_code}")
                print(f"   📝 错误内容: {response.text}")
                
        except Exception as e:
            results['chat'] = {'success': False, 'error': str(e)}
            print(f"   ❌ 聊天端点异常: {e}")
        
        return results
    
    async def test_websocket_connection(self) -> Dict[str, Any]:
        """测试WebSocket连接"""
        print("\n🔍 4. 测试WebSocket连接...")
        results = {}
        
        try:
            session_id = "test_session_123"
            ws_url = f"{self.ws_url}/ws/progress/{session_id}"
            print(f"   🔗 连接到: {ws_url}")
            
            async with websockets.connect(ws_url) as websocket:
                print("   ✅ WebSocket连接成功")
                
                # 接收初始消息
                initial_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                initial_data = json.loads(initial_message)
                
                # 发送心跳
                await websocket.send("ping")
                
                # 接收心跳响应
                response_message = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response_message)
                
                results['websocket'] = {
                    'success': True,
                    'initial_message': initial_data,
                    'heartbeat_response': response_data
                }
                
                print(f"   ✅ 初始消息: {initial_data.get('message', '')}")
                print(f"   ✅ 心跳响应: {response_data.get('message', '')}")
                
        except Exception as e:
            results['websocket'] = {'success': False, 'error': str(e)}
            print(f"   ❌ WebSocket连接失败: {e}")
        
        return results
    
    def test_from_frontend_perspective(self) -> Dict[str, Any]:
        """从前端角度测试连接"""
        print("\n🔍 5. 模拟前端请求...")
        results = {}
        
        try:
            # 模拟前端的完整请求
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000',  # RSHub前端可能的地址
                'Referer': 'http://localhost:3000/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            data = {
                "message": "什么是微波遥感？",
                "session_id": f"chat_{int(time.time())}_test",
                "token": "",  # 可能为空
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/agent/chat",
                headers=headers,
                json=data,
                timeout=15
            )
            
            results['frontend_simulation'] = {
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'headers': dict(response.headers),
                'response': response.json() if response.status_code == 200 else response.text
            }
            
            if response.status_code == 200:
                print(f"   ✅ 前端模拟请求成功: {response.status_code}")
            else:
                print(f"   ❌ 前端模拟请求失败: {response.status_code}")
                print(f"   📝 响应内容: {response.text}")
                
        except Exception as e:
            results['frontend_simulation'] = {'success': False, 'error': str(e)}
            print(f"   ❌ 前端模拟请求异常: {e}")
        
        return results
    
    async def run_full_diagnostic(self) -> Dict[str, Any]:
        """运行完整诊断"""
        print("🚀 开始RS Agent MCP前后端连接诊断...")
        print(f"🎯 目标服务器: {self.base_url}")
        print("=" * 60)
        
        all_results = {}
        
        # 基本连通性测试
        all_results['basic'] = self.test_server_basic()
        
        # CORS测试
        all_results['cors'] = self.test_cors_headers()
        
        # API端点测试
        all_results['api'] = self.test_agent_endpoints()
        
        # WebSocket测试
        all_results['websocket'] = await self.test_websocket_connection()
        
        # 前端模拟测试
        all_results['frontend'] = self.test_from_frontend_perspective()
        
        # 生成诊断报告
        self.generate_report(all_results)
        
        return all_results
    
    def generate_report(self, results: Dict[str, Any]):
        """生成诊断报告"""
        print("\n" + "=" * 60)
        print("📊 诊断报告")
        print("=" * 60)
        
        # 统计成功/失败
        total_tests = 0
        success_tests = 0
        
        for category, tests in results.items():
            for test_name, test_result in tests.items():
                total_tests += 1
                if test_result.get('success', False):
                    success_tests += 1
        
        print(f"📈 总体结果: {success_tests}/{total_tests} 项测试通过")
        
        # 详细分析
        print("\n🔍 详细分析:")
        
        if not results['basic']['health']['success']:
            print("❌ 关键问题: 服务器健康检查失败 - 请确认服务器是否正常运行")
        
        if not results['cors']['options']['success']:
            print("❌ CORS问题: 跨域配置可能有问题")
        
        if not results['api']['chat']['success']:
            print("❌ API问题: 聊天端点无法正常工作")
        
        if not results['websocket']['success']:
            print("❌ WebSocket问题: 实时进度功能将无法工作")
        
        if not results['frontend']['frontend_simulation']['success']:
            print("❌ 前端集成问题: 模拟前端请求失败")
        
        # 建议
        print("\n💡 建议:")
        
        # 检查是否所有测试都通过
        all_passed = True
        for category in results.values():
            for test in category.values():
                if not test.get('success', False):
                    all_passed = False
                    break
        
        if all_passed:
            print("✅ 所有测试通过！前后端连接正常。")
            print("   如果前端仍然无法连接，请检查:")
            print("   1. 前端是否运行在正确的端口上")
            print("   2. 浏览器控制台是否有JavaScript错误")
            print("   3. 前端的API URL配置是否正确")
        else:
            if not results['basic']['health']['success']:
                print("1. 确认RS Agent MCP服务器已在8000端口启动")
                print("2. 检查.env配置文件是否正确")
            
            if results['basic']['health']['success'] and not results['api']['chat']['success']:
                print("3. 检查API端点实现是否有问题")
                print("4. 查看服务器日志获取详细错误信息")
        
        print("\n📞 如需进一步帮助，请提供以上诊断结果。")

def main():
    """主函数"""
    print("🔧 RS Agent MCP 前后端连接诊断工具")
    print("=" * 60)
    
    # 可以通过命令行参数指定服务器地址
    import sys
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    diagnostic = ConnectionDiagnostic(base_url)
    
    # 运行诊断
    try:
        results = asyncio.run(diagnostic.run_full_diagnostic())
        
        # 保存结果到文件
        with open('diagnostic_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 详细结果已保存到: diagnostic_results.json")
        
    except KeyboardInterrupt:
        print("\n⛔ 诊断已取消")
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")

if __name__ == "__main__":
    main() 