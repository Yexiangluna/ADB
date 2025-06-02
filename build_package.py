#!/usr/bin/env python3
"""
ADB 项目打包脚本
支持 PyInstaller 打包为可执行文件
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def print_status(message, status="INFO"):
    """打印状态信息"""
    symbols = {
        "INFO": "ℹ️",
        "SUCCESS": "✅", 
        "ERROR": "❌",
        "WARNING": "⚠️"
    }
    print(f"{symbols.get(status, 'ℹ️')} {message}")

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__', '*.egg-info']
    
    for pattern in dirs_to_clean:
        if '*' in pattern:
            # 处理通配符
            import glob
            for path in glob.glob(pattern):
                if os.path.exists(path):
                    shutil.rmtree(path)
                    print_status(f"清理目录: {path}", "SUCCESS")
        else:
            if os.path.exists(pattern):
                shutil.rmtree(pattern)
                print_status(f"清理目录: {pattern}", "SUCCESS")

def check_dependencies():
    """检查并安装依赖"""
    print_status("检查项目依赖...")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print_status(f"PyInstaller 已安装 (版本: {PyInstaller.__version__})", "SUCCESS")
    except ImportError:
        print_status("安装 PyInstaller...", "INFO")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print_status("PyInstaller 安装完成", "SUCCESS")
      # 安装项目依赖
    if os.path.exists("requirements_clean.txt"):
        print_status("安装项目依赖...", "INFO")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements_clean.txt"], check=True)
        print_status("项目依赖安装完成", "SUCCESS")

def build_with_pyinstaller():
    """使用 PyInstaller 构建可执行文件"""
    print_status("开始 PyInstaller 打包...", "INFO")
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--clean",
        "--distpath", "dist",
        "--workpath", "build",
        "adb.spec"
    ]
    
    print_status(f"执行命令: {' '.join(cmd)}", "INFO")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_status("PyInstaller 打包成功!", "SUCCESS")
        print_status("输出目录: dist/ADB/", "INFO")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"PyInstaller 打包失败: {e.stderr}", "ERROR")
        return False

def create_single_exe():
    """创建单文件可执行程序"""
    print_status("创建单文件可执行程序...", "INFO")
    
    # 为 CLI 创建单文件版本
    cmd_cli = [
        "pyinstaller",
        "--onefile",
        "--name", "adb",
        "--distpath", "dist/single",
        "--clean",
        "adb_cli.py"
    ]
    
    # 为服务器创建单文件版本
    cmd_server = [
        "pyinstaller", 
        "--onefile",
        "--name", "adb-server",
        "--distpath", "dist/single", 
        "--clean",
        "adb_server.py"
    ]
    
    try:
        subprocess.run(cmd_cli, check=True, capture_output=True, text=True)
        print_status("CLI 单文件打包成功", "SUCCESS")
        
        subprocess.run(cmd_server, check=True, capture_output=True, text=True)
        print_status("服务器单文件打包成功", "SUCCESS")
        
        print_status("单文件可执行程序位于: dist/single/", "INFO")
        return True
    except subprocess.CalledProcessError as e:
        print_status(f"单文件打包失败: {e}", "ERROR")
        return False

def copy_additional_files():
    """复制额外的文件到发布目录"""
    print_status("复制额外文件...", "INFO")
    
    dist_dir = Path("dist/ADB")
    if not dist_dir.exists():
        print_status("发布目录不存在，跳过文件复制", "WARNING")
        return
    
    # 要复制的文件
    files_to_copy = [
        "README.md",
        "requirements.txt", 
        "config.py",
    ]
    
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy2(file_name, dist_dir)
            print_status(f"复制文件: {file_name}", "SUCCESS")
    
    # 复制示例目录
    if os.path.exists("examples"):
        shutil.copytree("examples", dist_dir / "examples", dirs_exist_ok=True)
        print_status("复制示例目录", "SUCCESS")

def create_startup_scripts():
    """创建启动脚本"""
    print_status("创建启动脚本...", "INFO")
    
    dist_dir = Path("dist/ADB")
    if not dist_dir.exists():
        return
    
    # Windows 批处理脚本
    bat_content = """@echo off
echo ADB 数据库管理系统
echo.
echo 可用命令:
echo   adb.exe --help          显示帮助信息
echo   adb-server.exe --help   显示服务器帮助
echo.
echo 示例:
echo   adb.exe list-tables     列出所有表
echo   adb-server.exe --port 8080  在端口8080启动服务器
echo.
pause
"""
    
    with open(dist_dir / "start.bat", "w", encoding="utf-8") as f:
        f.write(bat_content)
    
    print_status("创建 Windows 启动脚本", "SUCCESS")

def create_release_package():
    """创建发布包"""
    print_status("创建发布包...", "INFO")
    
    if not os.path.exists("dist/ADB"):
        print_status("找不到构建输出，无法创建发布包", "ERROR")
        return False
    
    # 创建 ZIP 包
    shutil.make_archive("ADB-Windows", "zip", "dist", "ADB")
    print_status("创建 ZIP 发布包: ADB-Windows.zip", "SUCCESS")
    
    return True

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ADB 项目打包工具")
    parser.add_argument("--clean", action="store_true", help="清理构建目录")
    parser.add_argument("--single", action="store_true", help="创建单文件可执行程序")
    parser.add_argument("--no-deps", action="store_true", help="跳过依赖检查")
    parser.add_argument("--package", action="store_true", help="创建发布包")
    
    args = parser.parse_args()
    
    print_status("ADB 项目打包工具", "INFO")
    print_status("=" * 50, "INFO")
    
    # 清理构建目录
    if args.clean:
        clean_build_dirs()
        return
    
    try:
        # 检查依赖
        if not args.no_deps:
            check_dependencies()
        
        # 清理旧的构建文件
        clean_build_dirs()
        
        # 构建主要的可执行文件
        if not build_with_pyinstaller():
            sys.exit(1)
        
        # 复制额外文件
        copy_additional_files()
        
        # 创建启动脚本
        create_startup_scripts()
        
        # 创建单文件版本
        if args.single:
            create_single_exe()
        
        # 创建发布包
        if args.package:
            create_release_package()
        
        print_status("=" * 50, "INFO")
        print_status("打包完成!", "SUCCESS")
        print_status("输出目录:", "INFO")
        print_status("  - 完整版本: dist/ADB/", "INFO")
        if args.single:
            print_status("  - 单文件版本: dist/single/", "INFO")
        if args.package:
            print_status("  - 发布包: ADB-Windows.zip", "INFO")
            
    except Exception as e:
        print_status(f"打包过程中出现错误: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
