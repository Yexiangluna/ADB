
"""
ADB 可执行文件打包脚本
使用 PyInstaller 和 cx_Freeze 两种方式
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✅ 清理目录: {dir_name}")

def build_with_pyinstaller():
    """使用 PyInstaller 打包"""
    print("=== 使用 PyInstaller 打包 ===")
    
    # 检查是否安装了 PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller 版本: {PyInstaller.__version__}")
    except ImportError:
        print("❌ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 创建 PyInstaller 规范文件
    create_pyinstaller_spec()
    
    # 构建可执行文件
    cmd = [
        "pyinstaller",
        "--clean",
        "--distpath", "dist/pyinstaller",
        "adb.spec"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ PyInstaller 打包成功")
        print(f"输出目录: dist/pyinstaller/")
    else:
        print(f"❌ PyInstaller 打包失败: {result.stderr}")

def create_pyinstaller_spec():
    """创建 PyInstaller 规范文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# ADB 主程序
adb_main = Analysis(
    ['adb_cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('.env.template', '.'),
        ('templates/', 'templates/'),
        ('examples/', 'examples/'),
    ],
    hiddenimports=['flask', 'dotenv', 'coloredlogs'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ADB 服务器程序
adb_server = Analysis(
    ['adb_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('.env.template', '.'),
        ('templates/', 'templates/'),
    ],
    hiddenimports=['flask', 'dotenv', 'coloredlogs'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

MERGE( (adb_main, 'adb_main', 'adb_main'), (adb_server, 'adb_server', 'adb_server') )

# 主程序可执行文件
pyz_main = PYZ(adb_main.pure, adb_main.zipped_data, cipher=block_cipher)
exe_main = EXE(
    pyz_main,
    adb_main.scripts,
    [],
    exclude_binaries=True,
    name='adb',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/adb.ico' if os.path.exists('assets/adb.ico') else None,
)

# 服务器程序可执行文件
pyz_server = PYZ(adb_server.pure, adb_server.zipped_data, cipher=block_cipher)
exe_server = EXE(
    pyz_server,
    adb_server.scripts,
    [],
    exclude_binaries=True,
    name='adb-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/adb.ico' if os.path.exists('assets/adb.ico') else None,
)

# 打包为目录
coll = COLLECT(
    exe_main,
    adb_main.binaries,
    adb_main.zipfiles,
    adb_main.datas,
    exe_server,
    adb_server.binaries,
    adb_server.zipfiles,
    adb_server.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ADB',
)
'''
    
    with open('adb.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("✅ 创建 PyInstaller 规范文件")

def build_with_cx_freeze():
    """使用 cx_Freeze 打包"""
    print("=== 使用 cx_Freeze 打包 ===")
    
    # 检查是否安装了 cx_Freeze
    try:
        import cx_Freeze
        print(f"cx_Freeze 版本: {cx_Freeze.version}")
    except ImportError:
        print("❌ cx_Freeze 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cx_freeze"])
    
    # 创建 cx_Freeze 设置脚本
    create_cx_freeze_setup()
    
    # 构建可执行文件
    cmd = [sys.executable, "setup_cx_freeze.py", "build"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ cx_Freeze 打包成功")
        print(f"输出目录: build/")
    else:
        print(f"❌ cx_Freeze 打包失败: {result.stderr}")

def create_cx_freeze_setup():
    """创建 cx_Freeze 设置文件"""
    setup_content = '''from cx_Freeze import setup, Executable
import sys
import os

# 包含的文件
include_files = [
    "config.json",
    ".env.template",
    ("templates/", "templates/"),
    ("examples/", "examples/"),
    ("data/", "data/"),
]

# 包含的包
packages = ["flask", "json", "os", "shutil", "logging", "time", "datetime", "pathlib"]

# 排除的包
excludes = ["tkinter", "unittest", "pydoc", "doctest"]

# 构建选项
build_exe_options = {
    "packages": packages,
    "excludes": excludes,
    "include_files": include_files,
    "include_msvcrt": True,
    "zip_include_packages": "*",
    "zip_exclude_packages": "",
}

# 可执行文件
executables = [
    Executable(
        "adb_cli.py",
        base="Console",
        target_name="adb.exe" if sys.platform == "win32" else "adb",
        icon="assets/adb.ico" if os.path.exists("assets/adb.ico") else None,
    ),
    Executable(
        "adb_server.py", 
        base="Console",
        target_name="adb-server.exe" if sys.platform == "win32" else "adb-server",
        icon="assets/adb.ico" if os.path.exists("assets/adb.ico") else None,
    ),
]

setup(
    name="ADB",
    version="1.0.0",
    description="ADB Database Management System",
    options={"build_exe": build_exe_options},
    executables=executables,
)
'''
    
    with open('setup_cx_freeze.py', 'w', encoding='utf-8') as f:
        f.write(setup_content)
    print("✅ 创建 cx_Freeze 设置文件")

def create_installers():
    """创建安装程序"""
    print("=== 创建安装程序 ===")
    
    # Windows NSIS 安装脚本
    if sys.platform == "win32":
        create_nsis_script()
    
    # Linux/Mac 安装脚本
    create_shell_installer()

def create_nsis_script():
    """创建 NSIS 安装脚本 (Windows)"""
    nsis_content = '''!define APPNAME "ADB Database"
!define COMPANYNAME "ADB Team"
!define DESCRIPTION "轻量级数据库管理系统"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/your-username/adb"
!define UPDATEURL "https://github.com/your-username/adb"
!define ABOUTURL "https://github.com/your-username/adb"

!define INSTALLSIZE 50000

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${APPNAME}"

Name "${APPNAME}"
Icon "assets\\adb.ico"
outFile "dist\\ADB-Installer.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "需要管理员权限安装此程序"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "ADB Core" SecCore
    setOutPath $INSTDIR
    
    # 复制文件
    file /r "dist\\pyinstaller\\ADB\\*"
    
    # 创建卸载程序
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    # 注册表项
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayIcon" "$INSTDIR\\adb.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd

section "Start Menu Shortcuts" SecStartMenu
    createDirectory "$SMPROGRAMS\\${APPNAME}"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\ADB.lnk" "$INSTDIR\\adb.exe"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\ADB Server.lnk" "$INSTDIR\\adb-server.exe"
    createShortCut "$SMPROGRAMS\\${APPNAME}\\Uninstall.lnk" "$INSTDIR\\uninstall.exe"
sectionEnd

section "Desktop Shortcuts" SecDesktop
    createShortCut "$DESKTOP\\ADB.lnk" "$INSTDIR\\adb.exe"
sectionEnd

section "Add to PATH" SecPath
    # 添加到系统PATH
    ReadRegStr $0 HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path"
    StrCpy $0 "$0;$INSTDIR"
    WriteRegStr HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path" "$0"
    SendMessage ${HWND_BROADCAST} ${WM_WININICHANGE} 0 "STR:Environment" /TIMEOUT=5000
sectionEnd

function un.onInit
    SetShellVarContext all
    MessageBox MB_OKCANCEL "确定要卸载 ${APPNAME}？" IDOK next
        Abort
    next:
    !insertmacro VerifyUserIsAdmin
functionEnd

section "uninstall"
    # 删除文件
    delete "$INSTDIR\\*.*"
    rmDir /r "$INSTDIR"
    
    # 删除快捷方式
    delete "$SMPROGRAMS\\${APPNAME}\\*.*"
    rmDir "$SMPROGRAMS\\${APPNAME}"
    delete "$DESKTOP\\ADB.lnk"
    
    # 删除注册表项
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${APPNAME}"
sectionEnd
'''
    
    os.makedirs('installers', exist_ok=True)
    with open('installers/adb_installer.nsi', 'w', encoding='utf-8') as f:
        f.write(nsis_content)
    print("✅ 创建 NSIS 安装脚本")

def create_shell_installer():
    """创建 Shell 安装脚本 (Linux/Mac)"""
    install_script = '''#!/bin/bash
# ADB 安装脚本

set -e

INSTALL_DIR="/opt/adb"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/adb"

echo "=== ADB 数据库安装程序 ==="

# 检查权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用 sudo 运行此安装程序"
    exit 1
fi

# 创建安装目录
echo "创建安装目录..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"

# 复制文件
echo "复制程序文件..."
cp -r build/exe.linux-*/* "$INSTALL_DIR/"

# 创建符号链接
echo "创建命令行工具..."
ln -sf "$INSTALL_DIR/adb" "$BIN_DIR/adb"
ln -sf "$INSTALL_DIR/adb-server" "$BIN_DIR/adb-server"

# 复制配置文件
echo "设置配置文件..."
cp config.json "$CONFIG_DIR/"
cp .env.template "$CONFIG_DIR/.env"

# 设置权限
chmod +x "$INSTALL_DIR/adb"
chmod +x "$INSTALL_DIR/adb-server"
chmod 644 "$CONFIG_DIR/config.json"
chmod 600 "$CONFIG_DIR/.env"

# 创建数据目录
mkdir -p /var/lib/adb/data
mkdir -p /var/lib/adb/backups
mkdir -p /var/log/adb

# 设置权限
chown -R $SUDO_USER:$SUDO_USER /var/lib/adb
chown -R $SUDO_USER:$SUDO_USER /var/log/adb

echo "✅ ADB 安装完成！"
echo ""
echo "使用方法："
echo "  adb --help       # 查看帮助"
echo "  adb-server       # 启动API服务器"
echo ""
echo "配置文件位置："
echo "  $CONFIG_DIR/config.json"
echo "  $CONFIG_DIR/.env"
echo ""
echo "数据目录："
echo "  /var/lib/adb/data"
echo "  /var/lib/adb/backups"
'''
    
    os.makedirs('installers', exist_ok=True)
    with open('installers/install.sh', 'w', encoding='utf-8') as f:
        f.write(install_script)
    os.chmod('installers/install.sh', 0o755)
    print("✅ 创建 Shell 安装脚本")

def package_portable():
    """创建便携版"""
    print("=== 创建便携版 ===")
    
    portable_dir = "dist/portable"
    os.makedirs(portable_dir, exist_ok=True)
    
    # 复制核心文件
    core_files = [
        "adb.py",
        "config.py", 
        "config.json",
        ".env.template",
        "requirements.txt",
        "Readme.md",
    ]
    
    for file in core_files:
        if os.path.exists(file):
            shutil.copy2(file, portable_dir)
    
    # 复制目录
    dirs_to_copy = ["examples", "templates"]
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, f"{portable_dir}/{dir_name}", exist_ok=True)
    
    # 创建启动脚本
    if sys.platform == "win32":
        start_script = '''@echo off
cd /d "%~dp0"
python adb_cli.py %*
'''
        with open(f"{portable_dir}/adb.bat", 'w') as f:
            f.write(start_script)
        
        server_script = '''@echo off
cd /d "%~dp0"
python adb_server.py %*
'''
        with open(f"{portable_dir}/adb-server.bat", 'w') as f:
            f.write(server_script)
    else:
        start_script = '''#!/bin/bash
cd "$(dirname "$0")"
python3 adb_cli.py "$@"
'''
        with open(f"{portable_dir}/adb", 'w') as f:
            f.write(start_script)
        os.chmod(f"{portable_dir}/adb", 0o755)
        
        server_script = '''#!/bin/bash
cd "$(dirname "$0")"
python3 adb_server.py "$@"
'''
        with open(f"{portable_dir}/adb-server", 'w') as f:
            f.write(server_script)
        os.chmod(f"{portable_dir}/adb-server", 0o755)
    
    # 创建使用说明
    readme_content = '''# ADB 便携版

这是 ADB 数据库的便携版本，无需安装即可使用。

## 系统要求

- Python 3.7 或更高版本
- pip (Python 包管理器)

## 快速开始

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 运行基本示例：
   ```
   python examples/basic_usage.py
   ```

3. 启动API服务器：
   ```
   python adb_server.py
   ```

## 命令行工具

Windows:
- `adb.bat --help`       # 查看帮助
- `adb-server.bat`       # 启动服务器

Linux/Mac:
- `./adb --help`         # 查看帮助  
- `./adb-server`         # 启动服务器

## 配置

编辑 `.env` 文件或 `config.json` 来修改配置。

## 支持

访问项目主页获取更多帮助和文档。
'''
    
    with open(f"{portable_dir}/README_PORTABLE.md", 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ 便携版创建完成: {portable_dir}")

def main():
    """主函数"""
    print("=== ADB 项目打包工具 ===\n")
    
    # 检查当前目录
    if not os.path.exists("adb.py"):
        print("❌ 请在 ADB 项目根目录运行此脚本")
        return
    
    # 清理旧的构建文件
    clean_build()
    
    # 创建必要的CLI文件
    create_cli_files()
    
    choice = input("""
选择打包方式：
1. PyInstaller (推荐，生成单个可执行文件)
2. cx_Freeze (跨平台兼容性好)
3. 便携版 (需要Python环境)
4. 全部打包
5. 只创建安装程序

请输入选择 (1-5): """)
    
    if choice == "1":
        build_with_pyinstaller()
    elif choice == "2": 
        build_with_cx_freeze()
    elif choice == "3":
        package_portable()
    elif choice == "4":
        build_with_pyinstaller()
        build_with_cx_freeze() 
        package_portable()
        create_installers()
    elif choice == "5":
        create_installers()
    else:
        print("❌ 无效选择")
        return
    
    print("\n=== 打包完成 ===")
    print("输出目录：")
    if os.path.exists("dist"):
        for item in os.listdir("dist"):
            print(f"  - dist/{item}")
    if os.path.exists("build"):
        print("  - build/")
    if os.path.exists("installers"):
        print("  - installers/")

def create_cli_files():
    """创建命令行接口文件"""
    # 创建主CLI文件
    cli_content = '''#!/usr/bin/env python3
"""
ADB 命令行接口
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from adb import ADB, ADBError

def main():
    parser = argparse.ArgumentParser(description="ADB 数据库命令行工具")
    parser.add_argument("--version", action="version", version="ADB 1.0.0")
    parser.add_argument("--db", default="adb_data.json", help="数据库文件路径")
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # 创建表命令
    create_parser = subparsers.add_parser("create-table", help="创建表")
    create_parser.add_argument("name", help="表名")
    create_parser.add_argument("--schema", help="表结构JSON文件")
    
    # 列出表命令
    list_parser = subparsers.add_parser("list-tables", help="列出所有表")
    
    # 插入数据命令
    insert_parser = subparsers.add_parser("insert", help="插入数据")
    insert_parser.add_argument("table", help="表名")
    insert_parser.add_argument("data", help="JSON格式数据")
    
    # 查询数据命令
    select_parser = subparsers.add_parser("select", help="查询数据")
    select_parser.add_argument("table", help="表名")
    select_parser.add_argument("--condition", help="查询条件JSON")
    select_parser.add_argument("--limit", type=int, help="限制结果数量")
    
    # 备份命令
    backup_parser = subparsers.add_parser("backup", help="备份数据库")
    backup_parser.add_argument("--path", help="备份文件路径")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        db = ADB(args.db, enable_logging=True)
        
        if args.command == "create-table":
            schema = None
            if args.schema:
                import json
                with open(args.schema, 'r') as f:
                    schema = json.load(f)
            success = db.create_table(args.name, schema)
            print(f"表 {args.name} {'创建成功' if success else '已存在'}")
            
        elif args.command == "list-tables":
            tables = db.list_tables()
            print("数据库表列表：")
            for table in tables:
                info = db.get_table_info(table)
                print(f"  - {table} ({info['record_count']} 条记录)")
                
        elif args.command == "insert":
            import json
            data = json.loads(args.data)
            success = db.insert(args.table, data)
            print(f"数据{'插入成功' if success else '插入失败'}")
            
        elif args.command == "select":
            condition = None
            if args.condition:
                import json
                condition = json.loads(args.condition)
            records = db.select(args.table, condition, args.limit)
            print(f"查询结果 ({len(records)} 条记录):")
            import json
            print(json.dumps(records, ensure_ascii=False, indent=2))
            
        elif args.command == "backup":
            success = db.backup(args.path)
            print(f"备份{'成功' if success else '失败'}")
            
    except ADBError as e:
        print(f"❌ ADB错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('adb_cli.py', 'w', encoding='utf-8') as f:
        f.write(cli_content)
    
    # 创建服务器文件
    server_content = '''#!/usr/bin/env python3
"""
ADB API 服务器启动脚本
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from adb import ADB, ADBAPIServer

def main():
    parser = argparse.ArgumentParser(description="ADB API 服务器")
    parser.add_argument("--host", default="127.0.0.1", help="服务器地址")
    parser.add_argument("--port", type=int, default=5000, help="服务器端口")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    parser.add_argument("--db", default="adb_data.json", help="数据库文件路径")
    parser.add_argument("--api-key", help="API访问密钥")
    
    args = parser.parse_args()
    
    try:
        # 创建数据库实例
        db = ADB(args.db, enable_logging=True)
        
        # 创建API服务器
        server = ADBAPIServer(db, api_key=args.api_key)
        
        print(f"ADB API服务器启动在 http://{args.host}:{args.port}")
        print(f"数据库: {db.db_path}")
        print(f"表数量: {len(db.list_tables())}")
        
        if args.api_key:
            print(f"API密钥验证: 启用")
        
        # 启动服务器
        server.run(host=args.host, port=args.port, debug=args.debug)
        
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    with open('adb_server.py', 'w', encoding='utf-8') as f:
        f.write(server_content)
    
    print("✅ 创建CLI文件")

if __name__ == "__main__":
    main()