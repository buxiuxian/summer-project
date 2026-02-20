#!/usr/bin/env python3
"""
RS Agent MCP 快速启动脚本
用于项目的快速初始化和启动
"""

import os
import sys
import subprocess
from pathlib import Path

# 知识库源目录列表
KNOWLEDGE_DIRS = [
    "file_storage/converted",
]

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    if sys.version_info < (3, 11):
        print("❌ 错误：需要Python 3.11或更高版本")
        print(f"   当前版本：{sys.version}")
        return False
    
    print(f"✅ Python版本：{sys.version}")
    
    # 检查是否在虚拟环境中
    if sys.prefix == sys.base_prefix:
        print("⚠️  警告：建议在虚拟环境中运行")
    else:
        print("✅ 运行在虚拟环境中")
    
    return True

def check_dependencies():
    """检查依赖是否安装"""
    print("📦 检查依赖...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'pydantic-settings'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包：{', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    return True

def setup_environment():
    """设置环境"""
    print("🔧 设置环境...")
    
    # 检查.env文件
    env_file = Path(".env")
    env_template = Path("env_template.txt")
    
    if not env_file.exists():
        if env_template.exists():
            print("📝 创建.env文件...")
            import shutil
            shutil.copy(env_template, env_file)
            print("✅ .env文件已创建，请编辑其中的API密钥")
        else:
            print("⚠️  警告：找不到环境变量模板文件")
    else:
        print("✅ .env文件已存在")
    
    # 创建必要的目录
    directories = [
        "file_storage/originals",
        "file_storage/converted", 
        "logs",
        "temp"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"📁 创建目录：{directory}")
        else:
            print(f"✅ 目录已存在：{directory}")

def initialize_knowledge_base():
    """初始化知识库"""
    print("📚 初始化知识库...")
    
    try:
        from app.rag.knowledge_base import build_domain_science_db
        build_domain_science_db()
        print("✅ 知识库初始化完成")
    except ImportError as e:
        print(f"⚠️  知识库初始化跳过（缺少依赖）：{e}")
    except Exception as e:
        print(f"⚠️  知识库初始化失败：{e}")

def start_server():
    """启动服务器"""
    print("🚀 启动RS Agent MCP服务器...")
    
    try:
        # 检查环境变量
        from app.core.config import settings
        
        # 检查LLM API密钥配置
        if not settings.API_KEY:
            print("⚠️  警告：未设置API_KEY，某些功能可能无法正常工作")
        
        # 检查端口是否被占用
        import socket
        port = settings.PORT
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  端口 {port} 被占用，尝试使用端口 {port + 1}")
            port = port + 1
        
        print(f"📡 服务器将在 http://{settings.HOST}:{port} 启动")
        print(f"📊 API文档: http://{settings.HOST}:{port}/docs")
        print(f"🔍 交互式API: http://{settings.HOST}:{port}/redoc")
        print(f"🌐 Web界面: http://localhost:{port}/static/index.html")
        print("\n按 Ctrl+C 停止服务器\n")
        
        # 在新线程中延迟打开浏览器
        import threading
        import time
        import webbrowser
        
        def open_browser():
            time.sleep(3)  # 等待服务器启动
            url = f"http://localhost:{port}/static/index.html"
            print(f"🌐 正在打开浏览器: {url}")
            webbrowser.open(url)
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动主应用
        import uvicorn
        
        # 使用导入字符串形式，而不是直接导入app对象
        uvicorn.run(
            "main:app",  # 使用根目录main.py中的app
            host=settings.HOST,
            port=port,
            reload=settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower()
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败：{e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 RS Agent MCP 快速启动")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print("\n💡 安装依赖：pip install -r requirements.txt")
        sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 初始化知识库
    initialize_knowledge_base()
    
    print("\n" + "=" * 50)
    print("✅ 初始化完成！")
    print("=" * 50)
    
    # 启动服务器
    start_server()

if __name__ == "__main__":
    main() 