#!/usr/bin/env python3
"""
知识库快速重置脚本
用于紧急情况下快速清空知识库的所有内容
无需用户确认，直接执行清理操作
"""

import os
import shutil
from pathlib import Path

def quick_reset():
    """快速重置知识库"""
    print("正在快速重置知识库...")
    
    # 1. 清空源文件目录
    source_dirs = [
        "file_storage/converted",
    ]
    
    for source_dir in source_dirs:
        if os.path.exists(source_dir):
            # 删除目录中的所有文件
            for file_path in Path(source_dir).rglob('*'):
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        print(f"删除源文件: {file_path}")
                    except Exception as e:
                        print(f"删除文件失败 {file_path}: {e}")
    
    # 2. 删除向量数据库文件
    db_files = [
        "faiss_index_domain_science.index",
        "faiss_index_domain_science_mapping.json",
        "tfidf_vectorizer.pkl",
        "tfidf_matrix.npy"
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            try:
                os.remove(db_file)
                print(f"删除数据库文件: {db_file}")
            except Exception as e:
                print(f"删除文件失败 {db_file}: {e}")
    
    # 3. 清理文件存储
    print("清理文件存储...")
    file_storage_paths = [
        "file_storage/originals",
        "file_storage/converted", 
        "file_storage/file_mapping.json"
    ]
    
    for storage_path in file_storage_paths:
        if os.path.exists(storage_path):
            try:
                if os.path.isfile(storage_path):
                    os.remove(storage_path)
                    print(f"删除文件存储文件: {storage_path}")
                elif os.path.isdir(storage_path):
                    shutil.rmtree(storage_path)
                    print(f"删除文件存储目录: {storage_path}")
            except Exception as e:
                print(f"删除文件存储项失败 {storage_path}: {e}")
    
    # 删除空的文件存储根目录
    if os.path.exists("file_storage"):
        try:
            if not os.listdir("file_storage"):
                os.rmdir("file_storage")
                print("删除空的文件存储根目录")
        except Exception as e:
            print(f"删除文件存储根目录失败: {e}")
    
    # 4. 清理缓存目录
    for pycache_dir in Path('.').rglob('__pycache__'):
        if pycache_dir.is_dir():
            try:
                shutil.rmtree(pycache_dir)
                print(f"删除缓存目录: {pycache_dir}")
            except Exception as e:
                print(f"删除缓存目录失败 {pycache_dir}: {e}")
    
    print("知识库快速重置完成！")

if __name__ == "__main__":
    quick_reset() 