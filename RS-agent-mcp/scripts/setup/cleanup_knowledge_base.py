#!/usr/bin/env python3
"""
知识库清理脚本
用于快速清空知识库中的全部内容，包括源文件和向量数据库
"""

import os
import shutil
import logging
from pathlib import Path
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.ConsoleHandler(),
        logging.FileHandler('cleanup_log.txt', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class KnowledgeBaseCleaner:
    """知识库清理器"""
    
    def __init__(self):
        # 知识库源文件路径
        self.source_paths = [
            "file_storage/converted",
        ]
        
        # 向量数据库文件
        self.vector_db_files = [
            "faiss_index_domain_science.index",
            "faiss_index_domain_science_mapping.json",
            "tfidf_vectorizer.pkl",
            "tfidf_matrix.npy"
        ]
        
        # 文件存储目录
        self.file_storage_paths = [
            "file_storage/originals",
            "file_storage/converted",
            "file_storage/file_mapping.json"
        ]
        
        # 日志文件
        self.log_files = [
            "logs"
        ]
        
        # 临时文件和缓存
        self.temp_files = [
            "__pycache__",
            "*.pyc",
            ".DS_Store",
            "Thumbs.db"
        ]
    
    def clean_source_files(self):
        """清理源文件"""
        logger.info("开始清理源文件...")
        
        for source_path in self.source_paths:
            if os.path.exists(source_path):
                try:
                    # 获取文件数量
                    file_count = len([f for f in Path(source_path).rglob('*') if f.is_file()])
                    
                    if file_count > 0:
                        logger.info(f"清理目录: {source_path} (包含 {file_count} 个文件)")
                        
                        # 删除目录中的所有文件，但保留目录结构
                        for file_path in Path(source_path).rglob('*'):
                            if file_path.is_file():
                                file_path.unlink()
                                logger.debug(f"删除文件: {file_path}")
                        
                        logger.info(f"成功清理目录: {source_path}")
                    else:
                        logger.info(f"目录 {source_path} 已经是空的")
                        
                except Exception as e:
                    logger.error(f"清理源文件目录 {source_path} 时出错: {str(e)}")
            else:
                logger.info(f"源文件目录 {source_path} 不存在，跳过")
    
    def clean_vector_db_files(self):
        """清理向量数据库文件"""
        logger.info("开始清理向量数据库文件...")
        
        deleted_files = []
        for file_path in self.vector_db_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    logger.info(f"删除向量数据库文件: {file_path}")
                except Exception as e:
                    logger.error(f"删除文件 {file_path} 时出错: {str(e)}")
            else:
                logger.debug(f"向量数据库文件 {file_path} 不存在，跳过")
        
        if deleted_files:
            logger.info(f"成功删除 {len(deleted_files)} 个向量数据库文件")
        else:
            logger.info("没有找到向量数据库文件")
    
    def clean_file_storage(self):
        """清理文件存储"""
        logger.info("开始清理文件存储...")
        
        deleted_items = []
        for storage_path in self.file_storage_paths:
            if os.path.exists(storage_path):
                try:
                    if os.path.isfile(storage_path):
                        os.remove(storage_path)
                        deleted_items.append(storage_path)
                        logger.info(f"删除文件存储文件: {storage_path}")
                    elif os.path.isdir(storage_path):
                        file_count = len([f for f in Path(storage_path).rglob('*') if f.is_file()])
                        if file_count > 0:
                            shutil.rmtree(storage_path)
                            deleted_items.append(f"{storage_path} ({file_count} 个文件)")
                            logger.info(f"删除文件存储目录: {storage_path} (包含 {file_count} 个文件)")
                        else:
                            logger.info(f"文件存储目录 {storage_path} 已经是空的")
                except Exception as e:
                    logger.error(f"删除文件存储项 {storage_path} 时出错: {str(e)}")
            else:
                logger.debug(f"文件存储路径 {storage_path} 不存在，跳过")
        
        # 如果文件存储根目录为空，也删除它
        if os.path.exists("file_storage"):
            try:
                if not os.listdir("file_storage"):
                    os.rmdir("file_storage")
                    deleted_items.append("file_storage (空目录)")
                    logger.info("删除空的文件存储根目录")
            except Exception as e:
                logger.error(f"删除文件存储根目录失败: {e}")
        
        if deleted_items:
            logger.info(f"成功清理 {len(deleted_items)} 个文件存储项")
        else:
            logger.info("没有找到文件存储项")
    
    def clean_log_files(self):
        """清理日志文件"""
        logger.info("开始清理日志文件...")
        
        for log_path in self.log_files:
            if os.path.exists(log_path):
                try:
                    if os.path.isdir(log_path):
                        # 清空日志目录但保留目录结构
                        file_count = len([f for f in Path(log_path).rglob('*') if f.is_file()])
                        if file_count > 0:
                            for file_path in Path(log_path).rglob('*'):
                                if file_path.is_file():
                                    file_path.unlink()
                            logger.info(f"清理日志目录: {log_path} (删除了 {file_count} 个文件)")
                        else:
                            logger.info(f"日志目录 {log_path} 已经是空的")
                    else:
                        # 删除单个日志文件
                        os.remove(log_path)
                        logger.info(f"删除日志文件: {log_path}")
                except Exception as e:
                    logger.error(f"清理日志文件 {log_path} 时出错: {str(e)}")
            else:
                logger.debug(f"日志路径 {log_path} 不存在，跳过")
    
    def clean_temp_files(self):
        """清理临时文件和缓存"""
        logger.info("开始清理临时文件和缓存...")
        
        # 递归查找并删除__pycache__目录
        for pycache_dir in Path('.').rglob('__pycache__'):
            if pycache_dir.is_dir():
                try:
                    shutil.rmtree(pycache_dir)
                    logger.info(f"删除缓存目录: {pycache_dir}")
                except Exception as e:
                    logger.error(f"删除缓存目录 {pycache_dir} 时出错: {str(e)}")
        
        # 删除.pyc文件
        for pyc_file in Path('.').rglob('*.pyc'):
            if pyc_file.is_file():
                try:
                    pyc_file.unlink()
                    logger.debug(f"删除pyc文件: {pyc_file}")
                except Exception as e:
                    logger.error(f"删除pyc文件 {pyc_file} 时出错: {str(e)}")
    
    def create_backup_report(self):
        """创建清理报告"""
        logger.info("创建清理报告...")
        
        report = {
            "cleanup_time": str(Path().resolve()),
            "source_directories": [],
            "vector_db_files": [],
            "existing_files_before_cleanup": []
        }
        
        # 检查源目录状态
        for source_path in self.source_paths:
            if os.path.exists(source_path):
                file_count = len([f for f in Path(source_path).rglob('*') if f.is_file()])
                report["source_directories"].append({
                    "path": source_path,
                    "exists": True,
                    "file_count": file_count
                })
            else:
                report["source_directories"].append({
                    "path": source_path,
                    "exists": False,
                    "file_count": 0
                })
        
        # 检查向量数据库文件状态
        for file_path in self.vector_db_files:
            report["vector_db_files"].append({
                "path": file_path,
                "exists": os.path.exists(file_path),
                "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0
            })
        
        # 保存报告
        try:
            with open('cleanup_report.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info("清理报告已保存到 cleanup_report.json")
        except Exception as e:
            logger.error(f"保存清理报告时出错: {str(e)}")
    
    def full_cleanup(self, include_logs=False):
        """执行完整清理"""
        logger.info("="*50)
        logger.info("开始执行知识库完整清理")
        logger.info("="*50)
        
        # 创建清理前的状态报告
        self.create_backup_report()
        
        # 执行各项清理
        self.clean_source_files()
        self.clean_vector_db_files()
        self.clean_file_storage()
        
        if include_logs:
            self.clean_log_files()
        
        self.clean_temp_files()
        
        logger.info("="*50)
        logger.info("知识库清理完成")
        logger.info("="*50)
        
        # 显示清理后的状态
        self.show_cleanup_summary()
    
    def show_cleanup_summary(self):
        """显示清理摘要"""
        logger.info("清理摘要:")
        
        # 检查源目录状态
        for source_path in self.source_paths:
            if os.path.exists(source_path):
                file_count = len([f for f in Path(source_path).rglob('*') if f.is_file()])
                logger.info(f"  {source_path}: {file_count} 个文件")
            else:
                logger.info(f"  {source_path}: 目录不存在")
        
        # 检查向量数据库文件状态
        existing_db_files = [f for f in self.vector_db_files if os.path.exists(f)]
        logger.info(f"剩余向量数据库文件: {len(existing_db_files)}")
        
        for file_path in existing_db_files:
            logger.info(f"  {file_path}: 存在")

def main():
    """主函数"""
    print("知识库清理工具")
    print("="*50)
    
    # 确认清理操作
    print("此操作将清空以下内容:")
    print("1. 所有源文件 (file_storage/converted)")
    print("2. 向量数据库文件 (.index, .json, .pkl, .npy)")
    print("3. 临时文件和缓存 (__pycache__, *.pyc)")
    print("4. 可选：日志文件 (logs/)")
    print()
    
    confirm = input("确认执行清理操作？(输入 'yes' 确认): ").strip().lower()
    
    if confirm != 'yes':
        print("操作已取消")
        return
    
    include_logs = input("是否同时清理日志文件？(输入 'yes' 确认): ").strip().lower() == 'yes'
    
    # 执行清理
    cleaner = KnowledgeBaseCleaner()
    cleaner.full_cleanup(include_logs=include_logs)
    
    print("\n清理完成！详细日志请查看 cleanup_log.txt")
    print("清理报告已保存到 cleanup_report.json")

if __name__ == "__main__":
    main() 