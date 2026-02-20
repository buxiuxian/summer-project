#!/usr/bin/env python3
"""
测试运行脚本
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests(test_type="all"):
    """运行测试"""
    project_root = Path(__file__).parent
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(project_root)
    
    if test_type == "unit":
        # 运行单元测试
        cmd = [sys.executable, "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
    elif test_type == "integration":
        # 运行集成测试
        cmd = [sys.executable, "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
    elif test_type == "all":
        # 运行所有测试
        cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]
    else:
        print(f"未知的测试类型: {test_type}")
        return False
    
    try:
        print(f"运行测试: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"运行测试时发生错误: {e}")
        return False

def run_coverage():
    """运行代码覆盖率测试"""
    project_root = Path(__file__).parent
    os.environ['PYTHONPATH'] = str(project_root)
    
    cmd = [sys.executable, "-m", "pytest", "tests/", "--cov=app", "--cov-report=html", "--cov-report=term-missing"]
    
    try:
        print(f"运行覆盖率测试: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"运行覆盖率测试时发生错误: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
    else:
        test_type = "all"
    
    if test_type == "coverage":
        success = run_coverage()
    else:
        success = run_tests(test_type)
    
    if success:
        print("✅ 测试通过!")
        sys.exit(0)
    else:
        print("❌ 测试失败!")
        sys.exit(1)