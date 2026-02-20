#!/usr/bin/env python3
"""
启动服务器并测试日志功能
"""

import subprocess
import time
import sys
import signal
import requests
import json

def start_server():
    """启动服务器"""
    print("🚀 启动服务器...")
    try:
        # 启动服务器
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(8)  # 等待更长时间确保服务器完全启动
        
        # 检查服务器是否启动成功
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ 服务器启动成功")
                return server_process
            else:
                print(f"❌ 服务器启动失败，状态码: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"❌ 无法连接到服务器: {e}")
            return None
            
    except Exception as e:
        print(f"❌ 启动服务器失败: {e}")
        return None

def test_chat_with_logs():
    """测试聊天功能并观察日志"""
    print("\n🧪 测试聊天功能...")
    
    try:
        # 发送一个简单的聊天请求
        chat_data = {
            "message": "什么是微波散射理论？",
            "stream": False
        }
        
        print("📤 发送聊天请求...")
        response = requests.post(
            "http://localhost:8000/api/v1/agent/chat", 
            json=chat_data,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 聊天请求成功")
            print(f"📋 任务类型: {data.get('task_type', 'N/A')}")
            print(f"📄 回答长度: {len(data.get('response', ''))}")
        else:
            print(f"❌ 聊天请求失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except Exception as e:
        print(f"❌ 测试聊天功能失败: {e}")

def test_log_endpoint():
    """测试日志端点"""
    print("\n🧪 测试日志端点...")
    
    try:
        response = requests.get("http://localhost:8000/api/v1/logs/test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ 日志测试端点成功")
            print(f"📊 队列大小: {data.get('queue_size', 'N/A')}")
            print(f"📝 发送日志数: {data.get('logs_sent', 'N/A')}")
        else:
            print(f"❌ 日志测试端点失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试日志端点失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("RS Agent 服务器启动和日志功能测试")
    print("=" * 60)
    
    # 启动服务器
    server_process = start_server()
    if not server_process:
        print("❌ 无法启动服务器，退出测试")
        sys.exit(1)
    
    try:
        # 测试日志端点
        test_log_endpoint()
        
        # 测试聊天功能
        test_chat_with_logs()
        
        print("\n📝 现在可以打开前端页面 http://localhost:8000/static/index.html")
        print("在右侧日志面板中观察实时日志")
        print("按 Ctrl+C 停止服务器")
        
        # 保持服务器运行
        try:
            server_process.wait()
        except KeyboardInterrupt:
            print("\n⏹ 停止服务器...")
            
    finally:
        # 停止服务器
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("✅ 服务器已停止")

if __name__ == "__main__":
    main() 