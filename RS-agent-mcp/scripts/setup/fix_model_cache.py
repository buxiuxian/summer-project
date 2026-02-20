#!/usr/bin/env python3
"""
修复模型缓存问题的专用脚本
"""

import os
import sys
import shutil
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clear_cache():
    """清理现有缓存"""
    cache_paths = [
        os.path.expanduser("~/.cache/huggingface/hub"),
        os.path.expanduser("~/.cache/torch/sentence_transformers"),
        os.path.expanduser("~/.cache/sentence_transformers"),
    ]
    
    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            print(f"清理缓存目录: {cache_path}")
            # 只删除sentence-transformers相关的模型
            try:
                for item in os.listdir(cache_path):
                    if "sentence-transformers" in item.lower():
                        item_path = os.path.join(cache_path, item)
                        if os.path.isdir(item_path):
                            print(f"  删除: {item}")
                            shutil.rmtree(item_path)
            except Exception as e:
                print(f"  清理失败: {e}")

def download_models_with_retry():
    """重新下载模型并确保完整性"""
    try:
        from sentence_transformers import SentenceTransformer
        
        # 强制联网模式
        os.environ.pop('HF_HUB_OFFLINE', None)
        os.environ.pop('TRANSFORMERS_OFFLINE', None)
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        
        models = [
            "all-MiniLM-L6-v2",
            "paraphrase-MiniLM-L6-v2",
            "paraphrase-multilingual-MiniLM-L12-v2"
        ]
        
        successful_models = []
        
        for model_name in models:
            print(f"\n正在下载模型: {model_name}")
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"  尝试 {attempt + 1}/{max_retries}")
                    
                    # 设置较长的超时时间
                    import socket
                    original_timeout = socket.getdefaulttimeout()
                    socket.setdefaulttimeout(300)  # 5分钟超时
                    
                    try:
                        # 强制重新下载
                        model = SentenceTransformer(model_name, cache_folder=None)
                        
                        # 测试模型
                        test_embedding = model.encode("测试文本")
                        print(f"  ✅ 下载成功，嵌入维度: {len(test_embedding)}")
                        
                        # 验证离线可用性
                        print(f"  验证离线可用性...")
                        
                        # 删除模型对象
                        del model
                        
                        # 尝试离线加载
                        os.environ['HF_HUB_OFFLINE'] = '1'
                        try:
                            offline_model = SentenceTransformer(model_name, local_files_only=True)
                            offline_embedding = offline_model.encode("离线测试")
                            print(f"  ✅ 离线验证成功")
                            del offline_model
                            successful_models.append(model_name)
                            break
                        except Exception as offline_e:
                            print(f"  ⚠️ 离线验证失败: {offline_e}")
                            print(f"  继续尝试...")
                        finally:
                            os.environ.pop('HF_HUB_OFFLINE', None)
                            
                    finally:
                        socket.setdefaulttimeout(original_timeout)
                        
                except Exception as e:
                    print(f"  ❌ 第{attempt + 1}次尝试失败: {str(e)[:100]}...")
                    if attempt < max_retries - 1:
                        print(f"  等待5秒后重试...")
                        import time
                        time.sleep(5)
                    else:
                        print(f"  放弃模型 {model_name}")
                        break
        
        print(f"\n下载完成:")
        print(f"成功下载的模型: {successful_models}")
        
        return len(successful_models) > 0
        
    except ImportError:
        print("❌ SentenceTransformers未安装")
        return False

def create_test_script():
    """创建一个简单的测试脚本"""
    test_script = """#!/usr/bin/env python3
import os
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)
    embedding = model.encode("测试文本")
    print(f"✅ 离线加载成功，维度: {len(embedding)}")
except Exception as e:
    print(f"❌ 离线加载失败: {e}")
"""
    
    with open("test/test_offline_simple.py", "w", encoding="utf-8") as f:
        f.write(test_script)
    
    print("✅ 创建了简单测试脚本: test/test_offline_simple.py")

def main():
    """主函数"""
    print("🔧 模型缓存修复工具")
    print("=" * 50)
    
    # 询问用户是否清理缓存
    print("是否清理现有的模型缓存? (y/N): ", end="")
    try:
        choice = input().strip().lower()
        if choice in ['y', 'yes']:
            clear_cache()
    except KeyboardInterrupt:
        print("\n操作取消")
        return
    
    # 重新下载模型
    print("\n开始重新下载模型...")
    success = download_models_with_retry()
    
    if success:
        print("\n✅ 模型下载成功!")
        create_test_script()
        print("\n可以运行以下命令测试:")
        print("python test/test_offline_simple.py")
    else:
        print("\n❌ 模型下载失败")
        print("建议:")
        print("1. 检查网络连接")
        print("2. 确认有足够的磁盘空间")
        print("3. 尝试使用代理或VPN")

if __name__ == "__main__":
    main() 