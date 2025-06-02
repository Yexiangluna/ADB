"""
ADB 测试运行脚本
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    """运行所有测试"""
    print("=== ADB 测试套件 ===\n")
    
    # 检查测试目录
    test_dir = Path(__file__).parent.parent / "tests"
    if not test_dir.exists():
        print("❌ 测试目录不存在")
        return
    
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print(f"\n=== 测试结果 ===")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n失败的测试:")
        for test, error in result.failures:
            print(f"  - {test}: {error}")
    
    if result.errors:
        print("\n错误的测试:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    # 返回退出码
    if result.failures or result.errors:
        sys.exit(1)
    else:
        print("\n✅ 所有测试通过!")
        sys.exit(0)

if __name__ == "__main__":
    main()
