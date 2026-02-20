#!/usr/bin/env python3
"""
RS Agent MCP 项目清理脚本

该脚本用于清理项目运行中产生的各种无用文件，确保项目在提交到GitHub时保持整洁。

使用方法:
    python clean_project.py

清理内容:
    - 临时文件和目录 (temp/, tmp/, *.tmp, *.log)
    - 缓存文件 (__pycache__, .pytest_cache, *.pyc)
    - 日志文件 (logs/)
    - 测试产生的文件 (htmlcov/, .coverage)
    - 知识库索引文件 (faiss_index_domain_science.index, faiss_index_domain_science_mapping.json)
    - 开发调试文件 (debug.md, progress.md)
    - 临时上传文件 (uploads/)
    - 旧的会话数据 (sessions/)
    - IDE配置文件 (.vscode/, .idea/)

重要说明:
    - .claude目录（用户个人设置）不会被清理
    - file_storage/ 目录不会被清理（包含用户上传的原始文件）
    - file_mapping.json 文件不会被清理（删除会导致上传文件丢失）
    - SentenceTransformer模型缓存位于用户目录，不会被清理
    - 项目记录文件默认保留，使用 --include-records 参数清理
    - 删除的索引文件可以通过重新构建知识库来重新生成
"""

import os
import shutil
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProjectCleaner:
    """项目清理器"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.cleaned_items = []
        self.failed_items = []
        
    def log_cleaned(self, item_type: str, path: str, size_mb: float = 0):
        """记录清理的项"""
        self.cleaned_items.append({
            'type': item_type,
            'path': str(path),
            'size_mb': size_mb,
            'timestamp': time.time()
        })
        
    def log_failed(self, item_type: str, path: str, error: str):
        """记录清理失败的项"""
        self.failed_items.append({
            'type': item_type,
            'path': str(path),
            'error': error,
            'timestamp': time.time()
        })
    
    def get_dir_size(self, path: Path) -> float:
        """获取目录大小（MB）"""
        try:
            if path.is_file():
                return path.stat().st_size / (1024 * 1024)
            elif path.is_dir():
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        file_path = os.path.join(dirpath, filename)
                        if os.path.exists(file_path):
                            total_size += os.path.getsize(file_path)
                return total_size / (1024 * 1024)
            return 0
        except (OSError, IOError):
            return 0
    
    def clean_temp_files(self) -> int:
        """清理临时文件"""
        logger.info("🧹 清理临时文件...")
        cleaned_count = 0
        
        temp_dirs = [
            self.project_root / "temp",
            self.project_root / "tmp",
        ]
        
        for temp_dir in temp_dirs:
            if temp_dir.exists():
                try:
                    size = self.get_dir_size(temp_dir)
                    shutil.rmtree(temp_dir)
                    temp_dir.mkdir(exist_ok=True)
                    self.log_cleaned("临时目录", temp_dir, size)
                    cleaned_count += 1
                    logger.info(f"  ✅ 已清理临时目录: {temp_dir.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("临时目录", temp_dir, str(e))
                    logger.error(f"  ❌ 清理临时目录失败 {temp_dir}: {e}")
        
        # 清理根目录下的临时文件
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.log",
            "*.cache",
            # 注意：.bak文件受到保护，不会在此清理
            "*.swp",
            "*.swo",
            "*~",
        ]
        
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        size = self.get_dir_size(file_path)
                        file_path.unlink()
                        self.log_cleaned("临时文件", file_path, size)
                        cleaned_count += 1
                        logger.info(f"  ✅ 已删除临时文件: {file_path.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("临时文件", file_path, str(e))
        
        return cleaned_count
    
    def clean_cache_files(self) -> int:
        """清理缓存文件"""
        logger.info("🧹 清理缓存文件...")
        cleaned_count = 0
        
        cache_dirs = [
            self.project_root / "__pycache__",
            self.project_root / ".pytest_cache",
            self.project_root / ".mypy_cache",
            self.project_root / ".ruff_cache",
        ]
        
        # 递归查找所有__pycache__目录
        for pycache_dir in self.project_root.rglob("__pycache__"):
            cache_dirs.append(pycache_dir)
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    size = self.get_dir_size(cache_dir)
                    shutil.rmtree(cache_dir)
                    self.log_cleaned("缓存目录", cache_dir, size)
                    cleaned_count += 1
                    logger.info(f"  ✅ 已清理缓存目录: {cache_dir.relative_to(self.project_root)} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("缓存目录", cache_dir, str(e))
                    logger.error(f"  ❌ 清理缓存目录失败 {cache_dir}: {e}")
        
        # 清理.pyc文件
        for pyc_file in self.project_root.rglob("*.pyc"):
            try:
                if pyc_file.is_file():
                    size = self.get_dir_size(pyc_file)
                    pyc_file.unlink()
                    self.log_cleaned("编译文件", pyc_file, size)
                    cleaned_count += 1
            except Exception as e:
                self.log_failed("编译文件", pyc_file, str(e))
        
        return cleaned_count
    
    def clean_model_files(self) -> int:
        """清理模型和索引文件（只删除可重新生成的文件）"""
        logger.info("🧹 清理模型和索引文件...")
        cleaned_count = 0
        
        # 注意：这些文件可以重新生成，删除后需要重新构建知识库
        safe_to_delete_patterns = [
            # FAISS向量索引文件（可以重新构建）
            "faiss_index_domain_science.index",            # 主索引文件
            "faiss_index_domain_science_mapping.json",     # 索引映射文件
            
            # 其他可能的索引文件（如果有）
            "*.index",                                    # 其他.index文件
            "faiss_index_*",                              # 其他FAISS索引文件
            
            # 机器学习模型文件（如果有）
            "*.pkl",                                      # Python pickle文件
            "*.pickle",                                   # Python pickle文件
        ]
        
        # 重要：不会被删除的文件
        protected_files = [
            "file_storage/file_mapping.json",             # 文件映射，删除会导致上传文件丢失
        ]
        
        for pattern in safe_to_delete_patterns:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        # 检查是否是受保护的文件
                        is_protected = False
                        for protected_file in protected_files:
                            if file_path.name == protected_file.split('/')[-1]:
                                is_protected = True
                                break
                        
                        if is_protected:
                            logger.info(f"  ⚠️  跳过受保护文件: {file_path.name}")
                            continue
                        
                        size = self.get_dir_size(file_path)
                        file_path.unlink()
                        self.log_cleaned("索引文件", file_path, size)
                        cleaned_count += 1
                        logger.info(f"  ✅ 已删除索引文件: {file_path.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("索引文件", file_path, str(e))
                    logger.error(f"  ❌ 删除索引文件失败 {file_path}: {e}")
        
        if cleaned_count > 0:
            logger.info("  💡 提示：删除的索引文件可以通过重新构建知识库来重新生成")
        
        return cleaned_count
    
    def clean_storage_files(self) -> int:
        """清理存储文件（只清理可重新生成的文件）"""
        logger.info("🧹 清理存储文件...")
        cleaned_count = 0
        
        # 重要：只清理可以安全删除的目录
        safe_to_clean_dirs = [
            # 注意：uploads/ 目录受到保护，不会在此清理
            # 注意：sessions/ 目录受到保护，不会在此清理
            self.project_root / "logs",         # 日志文件（可以重新生成）
        ]
        
        # 重要：不会清理的目录
        protected_dirs = [
            self.project_root / "file_storage", # 包含用户上传的原始文件，无法重新生成
            self.project_root / "uploads",      # 上传目录受到保护
            self.project_root / "sessions",     # 会话目录受到保护
        ]
        
        for storage_dir in safe_to_clean_dirs:
            if storage_dir.exists() and storage_dir.is_dir():
                try:
                    size = self.get_dir_size(storage_dir)
                    shutil.rmtree(storage_dir)
                    # 重新创建空目录
                    storage_dir.mkdir(exist_ok=True)
                    
                    self.log_cleaned("存储目录", storage_dir, size)
                    cleaned_count += 1
                    logger.info(f"  ✅ 已清理存储目录: {storage_dir.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("存储目录", storage_dir, str(e))
                    logger.error(f"  ❌ 清理存储目录失败 {storage_dir}: {e}")
        
        # 检查受保护的目录
        for protected_dir in protected_dirs:
            if protected_dir.exists():
                logger.info(f"  ⚠️  跳过受保护目录: {protected_dir.name} (包含用户上传文件)")
        
        return cleaned_count
    
    def clean_test_files(self) -> int:
        """清理测试产生的文件"""
        logger.info("🧹 清理测试文件...")
        cleaned_count = 0
        
        test_output_patterns = [
            # 注意：htmlcov/ 目录受到保护，不会在此清理
            ".coverage",
            ".coverage.*",
            "coverage.xml",
            "*.cover",
            "*.py,cover",
        ]
        
        for pattern in test_output_patterns:
            for path in self.project_root.glob(pattern):
                try:
                    if path.is_file():
                        size = self.get_dir_size(path)
                        path.unlink()
                        self.log_cleaned("测试文件", path, size)
                        cleaned_count += 1
                        logger.info(f"  ✅ 已删除测试文件: {path.name} ({size:.2f} MB)")
                    elif path.is_dir():
                        size = self.get_dir_size(path)
                        shutil.rmtree(path)
                        self.log_cleaned("测试目录", path, size)
                        cleaned_count += 1
                        logger.info(f"  ✅ 已删除测试目录: {path.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("测试文件", path, str(e))
                    logger.error(f"  ❌ 删除测试文件失败 {path}: {e}")
        
        return cleaned_count
    
    def clean_dev_files(self) -> int:
        """清理开发调试文件"""
        logger.info("🧹 清理开发调试文件...")
        cleaned_count = 0
        
        dev_files = [
            "debug.md",
            "debug_*.md",
            "progress.md", 
            "progress_*.md",
            "构建完成记录.md",
            "进度.md",
        ]
        
        for pattern in dev_files:
            for file_path in self.project_root.glob(pattern):
                try:
                    if file_path.is_file():
                        size = self.get_dir_size(file_path)
                        file_path.unlink()
                        self.log_cleaned("开发文件", file_path, size)
                        cleaned_count += 1
                        logger.info(f"  ✅ 已删除开发文件: {file_path.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("开发文件", file_path, str(e))
                    logger.error(f"  ❌ 删除开发文件失败 {file_path}: {e}")
        
        return cleaned_count
    
    def clean_project_records(self) -> int:
        """清理项目记录文件（可选）"""
        logger.info("🧹 清理项目记录文件...")
        cleaned_count = 0
        
        # 注意：项目记录/ 目录受到保护，不会在此清理
        logger.info("  ⚠️  项目记录目录受到保护，不会被清理")
        
        return cleaned_count
    
    def clean_ai_config(self) -> int:
        """清理AI相关配置（跳过.claude目录）"""
        logger.info("🧹 清理AI配置文件...")
        cleaned_count = 0
        
        # 注意：.claude目录包含用户个人设置，跳过清理
        logger.info("  ℹ️  跳过.claude目录（用户个人设置）")
        
        return cleaned_count
    
    def clean_ide_files(self) -> int:
        """清理IDE配置文件"""
        logger.info("🧹 清理IDE配置文件...")
        cleaned_count = 0
        
        ide_dirs = [
            self.project_root / ".vscode",
            self.project_root / ".idea",
        ]
        
        for ide_dir in ide_dirs:
            if ide_dir.exists():
                try:
                    size = self.get_dir_size(ide_dir)
                    shutil.rmtree(ide_dir)
                    self.log_cleaned("IDE配置", ide_dir, size)
                    cleaned_count += 1
                    logger.info(f"  ✅ 已清理IDE配置目录: {ide_dir.name} ({size:.2f} MB)")
                except Exception as e:
                    self.log_failed("IDE配置", ide_dir, str(e))
                    logger.error(f"  ❌ 清理IDE配置失败 {ide_dir}: {e}")
        
        return cleaned_count
    
    def generate_report(self) -> Dict[str, Any]:
        """生成清理报告"""
        total_size = sum(item['size_mb'] for item in self.cleaned_items)
        total_items = len(self.cleaned_items)
        
        report = {
            'summary': {
                'total_items_cleaned': total_items,
                'total_size_mb': total_size,
                'failed_items': len(self.failed_items),
                'timestamp': time.time()
            },
            'cleaned_items': self.cleaned_items,
            'failed_items': self.failed_items
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]):
        """打印清理报告"""
        summary = report['summary']
        
        print("\n" + "="*60)
        print("🧹 项目清理报告")
        print("="*60)
        print(f"✅ 清理项目数: {summary['total_items_cleaned']}")
        print(f"💾 释放空间: {summary['total_size_mb']:.2f} MB")
        print(f"❌ 失败项目: {summary['failed_items']}")
        print("="*60)
        
        if summary['failed_items'] > 0:
            print("\n⚠️  清理失败的项目:")
            for item in report['failed_items']:
                print(f"  - {item['type']}: {item['path']} ({item['error']})")
        
        print("\n🎉 项目清理完成！现在可以安全地提交到GitHub了。")
    
    def clean_all(self, include_records: bool = False) -> Dict[str, Any]:
        """执行全面清理"""
        logger.info("🚀 开始项目清理...")
        start_time = time.time()
        
        # 执行各种清理
        self.clean_temp_files()
        self.clean_cache_files()
        self.clean_model_files()
        self.clean_storage_files()
        self.clean_test_files()
        self.clean_dev_files()
        self.clean_ai_config()
        self.clean_ide_files()
        
        # 注意：项目记录目录现在受到保护，不再清理
        # 即使使用 --include-records 参数也不会清理项目记录
        
        # 生成报告
        report = self.generate_report()
        report['summary']['execution_time'] = time.time() - start_time
        
        # 打印报告
        self.print_report(report)
        
        return report


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RS Agent MCP 项目清理工具")
    parser.add_argument(
        "--include-records", 
        action="store_true",
        help="同时清理项目记录文件"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="项目根目录路径"
    )
    
    args = parser.parse_args()
    
    # 创建清理器
    cleaner = ProjectCleaner(args.project_root)
    
    # 执行清理
    try:
        report = cleaner.clean_all(include_records=args.include_records)
        
        # 退出码
        exit_code = 0 if report['summary']['failed_items'] == 0 else 1
        exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("⚠️  清理被用户中断")
        exit(1)
    except Exception as e:
        logger.error(f"❌ 清理过程中发生错误: {e}")
        exit(1)


if __name__ == "__main__":
    main()