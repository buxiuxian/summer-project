#!/usr/bin/env python3
"""
预下载和缓存sentence-transformers模型

这个脚本会：
1. 下载常用的embedding模型到本地缓存
2. 测试模型是否正常工作
3. 为RAG系统提供离线模型支持
4. 显示详细的下载和测试信息
"""

import os
import sys
import logging
import time
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查必要的依赖包"""
    try:
        import sentence_transformers
        logger.info(f"SentenceTransformers 版本: {sentence_transformers.__version__}")
        return True
    except ImportError:
        logger.error("SentenceTransformers未安装，请运行: pip install sentence-transformers")
        return False

def download_models():
    """下载并缓存embedding模型"""
    
    if not check_dependencies():
        return False
    
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("开始下载模型...")
    except ImportError:
        logger.error("SentenceTransformers导入失败")
        return False
    
    # 设置环境变量确保完整下载
    import os
    original_offline = os.environ.get('HF_HUB_OFFLINE', None)
    original_disable_telemetry = os.environ.get('HF_HUB_DISABLE_TELEMETRY', None)
    
    # 按优先级排序的模型列表（与RAG系统中的顺序保持一致）
    models_to_download = [
        # 小型高效模型（推荐）
        "all-MiniLM-L6-v2",  # 22MB，英文，速度快
        "paraphrase-MiniLM-L6-v2",  # 22MB，英文，备选
        
        # 多语言支持模型
        "paraphrase-multilingual-MiniLM-L12-v2",  # 多语言支持
        "distiluse-base-multilingual-cased",  # 多语言备选
        
        # 更大的模型（如果前面的都失败）
        "all-MiniLM-L12-v2",  # 稍大但效果更好
    ]
    
    successfully_downloaded = []
    failed_downloads = []
    
    try:
        # 确保联网模式下载
        os.environ['HF_HUB_OFFLINE'] = '0'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        
        for i, model_name in enumerate(models_to_download, 1):
            try:
                logger.info(f"[{i}/{len(models_to_download)}] 正在下载模型: {model_name}")
                start_time = time.time()
                
                # 设置更长的超时时间
                import socket
                original_timeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(180)  # 3分钟超时
                
                try:
                    # 下载模型（会自动缓存到用户目录）
                    # 先尝试强制重新下载以确保完整性
                    model = SentenceTransformer(model_name, use_auth_token=False)
                    download_time = time.time() - start_time
                    
                    # 测试模型
                    test_text = "这是一个测试句子。This is a test sentence."
                    test_start = time.time()
                    embedding = model.encode(test_text)
                    test_time = time.time() - test_start
                    
                    logger.info(f"✓ 成功下载并测试模型: {model_name}")
                    logger.info(f"  - 下载时间: {download_time:.2f}秒")
                    logger.info(f"  - 测试时间: {test_time:.4f}秒")
                    logger.info(f"  - 嵌入维度: {len(embedding)}")
                    
                    # 验证离线可用性
                    try:
                        logger.info(f"  - 验证离线可用性...")
                        # 临时设置离线模式测试
                        os.environ['HF_HUB_OFFLINE'] = '1'
                        offline_model = SentenceTransformer(model_name, local_files_only=True)
                        offline_embedding = offline_model.encode("离线测试")
                        logger.info(f"  ✓ 离线模式验证成功")
                        os.environ['HF_HUB_OFFLINE'] = '0'  # 恢复联网模式
                    except Exception as offline_e:
                        logger.warning(f"  ⚠️ 离线验证失败: {offline_e}")
                        logger.info(f"  - 重新下载确保完整性...")
                        # 重新下载
                        model = SentenceTransformer(model_name, use_auth_token=False)
                    
                    # 获取模型缓存路径
                    try:
                        cache_folder = getattr(model, 'cache_folder', None)
                        if cache_folder:
                            logger.info(f"  - 缓存路径: {cache_folder}")
                        else:
                            logger.info(f"  - 模型已缓存到默认位置")
                    except:
                        logger.info(f"  - 模型已缓存到默认位置")
                    
                    successfully_downloaded.append({
                        'name': model_name,
                        'download_time': download_time,
                        'test_time': test_time,
                        'embedding_dim': len(embedding)
                    })
                    
                finally:
                    socket.setdefaulttimeout(original_timeout)
                    
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"✗ 下载模型 {model_name} 失败: {error_msg}")
                
                # 提供具体的错误建议
                if "timeout" in error_msg.lower() or "connection" in error_msg.lower():
                    logger.warning(f"  建议: 检查网络连接，稍后重试")
                elif "disk" in error_msg.lower() or "space" in error_msg.lower():
                    logger.warning(f"  建议: 检查磁盘空间")
                
                failed_downloads.append({
                    'name': model_name,
                    'error': error_msg
                })
                continue
    
    finally:
        # 恢复原始环境变量
        if original_offline is not None:
            os.environ['HF_HUB_OFFLINE'] = original_offline
        else:
            os.environ.pop('HF_HUB_OFFLINE', None)
            
        if original_disable_telemetry is not None:
            os.environ['HF_HUB_DISABLE_TELEMETRY'] = original_disable_telemetry
        else:
            os.environ.pop('HF_HUB_DISABLE_TELEMETRY', None)
    
    # 显示下载总结
    print("\n" + "="*60)
    if successfully_downloaded:
        logger.info(f"✅ 成功下载 {len(successfully_downloaded)} 个模型:")
        for model in successfully_downloaded:
            logger.info(f"  - {model['name']} (维度: {model['embedding_dim']}, 下载: {model['download_time']:.2f}s)")
        
        # 推荐最佳模型
        recommended = successfully_downloaded[0]['name']
        logger.info(f"推荐使用模型: {recommended}")
        
    if failed_downloads:
        logger.warning(f"❌ {len(failed_downloads)} 个模型下载失败:")
        for model in failed_downloads:
            logger.warning(f"  - {model['name']}: {model['error'][:100]}...")
    
    if successfully_downloaded:
        return True
    else:
        logger.error("没有成功下载任何模型")
        return False

def check_cache_location():
    """检查模型缓存位置"""
    try:
        import os
        from pathlib import Path
        
        # HuggingFace缓存通常在用户目录下
        possible_cache_paths = [
            os.path.expanduser("~/.cache/huggingface/hub"),
            os.path.expanduser("~/.cache/torch/sentence_transformers"),
            os.path.expanduser("~/.cache/sentence_transformers"),
        ]
        
        found_cache = False
        for cache_path in possible_cache_paths:
            if os.path.exists(cache_path):
                logger.info(f"找到模型缓存目录: {cache_path}")
                found_cache = True
                
                # 列出已缓存的模型
                cached_models = []
                try:
                    for item in os.listdir(cache_path):
                        item_path = os.path.join(cache_path, item)
                        if os.path.isdir(item_path) and "sentence-transformers" in item:
                            cached_models.append(item)
                    
                    if cached_models:
                        logger.info("已缓存的sentence-transformers模型:")
                        for model in cached_models:
                            # 获取模型文件夹大小
                            try:
                                model_path = os.path.join(cache_path, model)
                                size = get_folder_size(model_path)
                                size_mb = size / (1024 * 1024)
                                logger.info(f"  - {model} ({size_mb:.1f}MB)")
                            except:
                                logger.info(f"  - {model}")
                    else:
                        logger.info("缓存目录中暂无sentence-transformers模型")
                except Exception as e:
                    logger.warning(f"读取缓存目录失败: {e}")
                break
        
        if not found_cache:
            logger.info("未找到标准缓存目录，模型将在首次使用时下载")
            
    except Exception as e:
        logger.error(f"检查缓存位置失败: {e}")

def get_folder_size(folder_path):
    """计算文件夹大小"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
    except:
        pass
    return total_size

def test_model_loading():
    """测试模型加载性能"""
    try:
        from sentence_transformers import SentenceTransformer
        import time
        
        test_models = [
            "all-MiniLM-L6-v2",
            "paraphrase-multilingual-MiniLM-L12-v2"
        ]
        
        for model_name in test_models:
            try:
                logger.info(f"测试加载模型: {model_name}")
                start_time = time.time()
                
                model = SentenceTransformer(model_name)
                load_time = time.time() - start_time
                
                # 测试编码
                test_texts = [
                    "测试文本",
                    "This is a test sentence",
                    "微波遥感技术应用"
                ]
                
                start_time = time.time()
                embeddings = model.encode(test_texts)
                encode_time = time.time() - start_time
                
                logger.info(f"  ✓ 加载时间: {load_time:.2f}秒")
                logger.info(f"  ✓ 编码时间: {encode_time:.4f}秒 (3个文本)")
                logger.info(f"  ✓ 嵌入维度: {len(embeddings[0])}")
                
            except Exception as e:
                logger.warning(f"  ✗ 测试失败: {e}")
                
    except ImportError:
        logger.error("SentenceTransformers未安装")

def show_system_info():
    """显示系统信息"""
    import platform
    import sys
    
    logger.info("系统信息:")
    logger.info(f"  - 操作系统: {platform.system()} {platform.release()}")
    logger.info(f"  - Python版本: {sys.version.split()[0]}")
    logger.info(f"  - 架构: {platform.machine()}")
    
    # 检查可用磁盘空间
    try:
        import shutil
        cache_dir = os.path.expanduser("~/.cache")
        total, used, free = shutil.disk_usage(cache_dir)
        free_gb = free / (1024**3)
        logger.info(f"  - 可用磁盘空间: {free_gb:.1f}GB")
    except:
        pass

def main():
    """主函数"""
    print("=" * 60)
    print("Sentence Transformers 模型预下载工具")
    print("=" * 60)
    
    # 显示系统信息
    logger.info("步骤0: 系统信息检查")
    show_system_info()
    print()
    
    # 1. 检查缓存位置
    logger.info("步骤1: 检查模型缓存位置")
    check_cache_location()
    print()
    
    # 2. 下载模型
    logger.info("步骤2: 下载embedding模型")
    success = download_models()
    print()
    
    if success:
        # 3. 测试模型加载
        logger.info("步骤3: 测试模型加载性能")
        test_model_loading()
        print()
        
        print("=" * 60)
        print("✅ 模型预下载完成！")
        print("")
        print("现在可以离线使用embedding模型了。")
        print("启动服务器时将自动使用本地缓存的模型。")
        print("")
        print("提示: 如需查看详细使用说明，请参阅 guide/模型预下载说明.md")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ 模型预下载失败！")
        print("")
        print("可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 确认有足够的磁盘空间 (至少200MB)")
        print("3. 安装必要依赖: pip install sentence-transformers")
        print("4. 稍后重试")
        print("=" * 60)

if __name__ == "__main__":
    main() 