"""
ADB 项目发布脚本
自动化版本发布、打包和分发
"""

import os
import sys
import subprocess
import shutil
import zipfile
import tarfile
from datetime import datetime
from pathlib import Path

VERSION = "1.0.0"
RELEASE_DATE = datetime.now().strftime("%Y-%m-%d")

def create_release_notes():
    """创建发布说明"""
    notes = f"""# ADB Database v{VERSION} 发布说明

发布日期: {RELEASE_DATE}

## ✨ 新增功能
- 完整的CRUD操作支持
- 索引系统提高查询性能
- 事务处理确保数据一致性
- Web API服务接口
- 数据验证和表结构管理
- 配置管理系统
- 完整测试套件

## 🛠️ 改进
- 原子写入确保数据安全
- 批量操作支持
- 详细错误处理
- 性能优化

## 📦 分发包
- Windows 可执行文件
- Linux 可执行文件
- macOS 应用程序
- 便携版 (所有平台)
- 源码包

## 📋 系统要求
- Python 3.7+ (便携版)
- 无需Python环境 (可执行文件版本)

## 🚀 快速开始
1. 下载适合您平台的版本
2. 运行 `adb --help` 查看使用说明
3. 启动API服务器: `adb-server`

## 📚 文档
- 使用手册: README.md
- API文档: 见项目主页
- 示例代码: examples/ 目录

## 🐛 已知问题
- 大型数据集 (>10万记录) 性能可能下降
- 并发访问支持有限

## 🔧 技术支持
- GitHub Issues
- 项目主页
- 开发者邮箱

---
完整更新日志请查看 CHANGELOG.md
"""
    
    with open('RELEASE_NOTES.md', 'w', encoding='utf-8') as f:
        f.write(notes)
    print("✅ 创建发布说明")

def create_archives():
    """创建分发压缩包"""
    print("创建分发压缩包...")
    
    release_dir = f"releases/adb-{VERSION}"
    os.makedirs(release_dir, exist_ok=True)
    
    # Windows 可执行文件包
    if os.path.exists("dist/pyinstaller/ADB"):
        with zipfile.ZipFile(f"{release_dir}/adb-{VERSION}-windows-x64.zip", 'w') as zf:
            for root, dirs, files in os.walk("dist/pyinstaller/ADB"):
                for file in files:
                    file_path = os.path.join(root, file)
                    zf.write(file_path, file_path.replace("dist/pyinstaller/ADB/", ""))
        print("✅ Windows 可执行文件包")
    
    # 便携版包
    if os.path.exists("dist/portable"):
        # Windows 便携版
        with zipfile.ZipFile(f"{release_dir}/adb-{VERSION}-portable-windows.zip", 'w') as zf:
            for root, dirs, files in os.walk("dist/portable"):
                for file in files:
                    file_path = os.path.join(root, file)
                    zf.write(file_path, file_path.replace("dist/portable/", ""))
        
        # Linux/Mac 便携版
        with tarfile.open(f"{release_dir}/adb-{VERSION}-portable-unix.tar.gz", 'w:gz') as tf:
            tf.add("dist/portable", arcname=".")
        print("✅ 便携版包")
    
    # 源码包
    source_files = [
        "adb.py", "config.py", "requirements.txt", "README.md",
        "setup.py", "adb_cli.py", "adb_server.py"
    ]
    source_dirs = ["examples", "tests", "templates"]
    
    with zipfile.ZipFile(f"{release_dir}/adb-{VERSION}-source.zip", 'w') as zf:
        for file in source_files:
            if os.path.exists(file):
                zf.write(file)
        for dir_name in source_dirs:
            if os.path.exists(dir_name):
                for root, dirs, files in os.walk(dir_name):
                    for file in files:
                        zf.write(os.path.join(root, file))
    
    with tarfile.open(f"{release_dir}/adb-{VERSION}-source.tar.gz", 'w:gz') as tf:
        for file in source_files:
            if os.path.exists(file):
                tf.add(file)
        for dir_name in source_dirs:
            if os.path.exists(dir_name):
                tf.add(dir_name)
    
    print("✅ 源码包")

def generate_checksums():
    """生成校验和文件"""
    import hashlib
    
    release_dir = f"releases/adb-{VERSION}"
    checksums = []
    
    for file in os.listdir(release_dir):
        if file.endswith(('.zip', '.tar.gz', '.exe')):
            file_path = os.path.join(release_dir, file)
            
            # SHA256
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            checksums.append(f"{sha256_hash.hexdigest()}  {file}")
    
    with open(f"{release_dir}/SHA256SUMS.txt", 'w') as f:
        f.write("\n".join(checksums))
    
    print("✅ 生成校验和文件")

def main():
    """主发布流程"""
    print(f"=== ADB v{VERSION} 发布流程 ===\n")
    
    # 检查当前目录
    if not os.path.exists("adb.py"):
        print("❌ 请在 ADB 项目根目录运行此脚本")
        return
    
    # 运行测试
    print("1. 运行测试...")
    if os.path.exists("tests"):
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], 
                              capture_output=True)
        if result.returncode != 0:
            print("❌ 测试失败，停止发布")
            return
        print("✅ 所有测试通过")
    
    # 清理旧版本
    print("2. 清理旧版本...")
    if os.path.exists("releases"):
        shutil.rmtree("releases")
    
    # 打包
    print("3. 开始打包...")
    subprocess.run([sys.executable, "build_exe.py"])
    
    # 创建发布说明
    print("4. 创建发布说明...")
    create_release_notes()
    
    # 创建压缩包
    print("5. 创建分发包...")
    create_archives()
    
    # 生成校验和
    print("6. 生成校验和...")
    generate_checksums()
    
    print(f"\n=== 发布完成 ===")
    print(f"版本: {VERSION}")
    print(f"发布目录: releases/adb-{VERSION}/")
    print(f"分发包:")
    
    release_dir = f"releases/adb-{VERSION}"
    for file in os.listdir(release_dir):
        print(f"  - {file}")

if __name__ == "__main__":
    main()
