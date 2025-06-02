"""
ADB 安装和设置脚本
"""

import os
import sys
import json
import shutil
from pathlib import Path

def create_directory_structure():
    """创建项目目录结构"""
    directories = [
        "data",
        "backups", 
        "logs",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ 创建目录: {directory}")

def create_default_config():
    """创建默认配置文件"""
    config = {
        "database": {
            "path": "./data/adb_database.json",
            "backup_dir": "./backups",
            "auto_backup_interval": 3600,
            "max_records_per_table": 100000
        },
        "api": {
            "host": "127.0.0.1",
            "port": 5000,
            "debug": False,
            "api_key": "change-this-secret-key",
            "require_api_key": True,
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60
            }
        },
        "logging": {
            "level": "INFO",
            "file": "./logs/adb.log",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    config_path = "config.json"
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        print(f"✅ 创建配置文件: {config_path}")
    else:
        print(f"ℹ️ 配置文件已存在: {config_path}")

def create_env_template():
    """创建环境变量模板"""
    env_template = """# ADB 环境配置模板
# 复制此文件为 .env 并修改相应值

# 数据库配置
ADB_DATABASE_PATH=./data/adb_database.json
ADB_BACKUP_DIR=./backups
ADB_LOG_LEVEL=INFO

# API服务器配置  
ADB_API_HOST=127.0.0.1
ADB_API_PORT=5000
ADB_API_DEBUG=False
ADB_API_KEY=your-super-secret-api-key-here

# 性能配置
ADB_MAX_RECORDS_PER_TABLE=100000

# 安全配置
ADB_REQUIRE_API_KEY=True
"""
    
    env_path = ".env.template"
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_template)
    print(f"✅ 创建环境变量模板: {env_path}")

def install_dependencies():
    """安装依赖包"""
    try:
        import subprocess
        
        # 检查requirements.txt是否存在
        if os.path.exists("requirements.txt"):
            print("安装依赖包...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 依赖包安装成功")
            else:
                print(f"❌ 依赖包安装失败: {result.stderr}")
        else:
            print("ℹ️ 未找到 requirements.txt 文件")
            
    except Exception as e:
        print(f"❌ 安装依赖包时出错: {e}")

def run_tests():
    """运行测试"""
    try:
        import subprocess
        
        if os.path.exists("tests"):
            print("运行测试...")
            result = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 所有测试通过")
                print(result.stdout)
            else:
                print(f"❌ 测试失败: {result.stderr}")
        else:
            print("ℹ️ 未找到测试目录")
            
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")

def main():
    """主安装流程"""
    print("=== ADB 项目设置 ===\n")
    
    print("1. 创建目录结构")
    create_directory_structure()
    print()
    
    print("2. 创建配置文件")
    create_default_config()
    create_env_template()
    print()
    
    print("3. 安装依赖")
    install_dependencies()
    print()
    
    print("4. 运行测试")
    run_tests()
    print()
    
    print("=== 设置完成 ===")
    print("\n下一步:")
    print("1. 复制 .env.template 为 .env 并修改配置")
    print("2. 修改 config.json 中的配置项")
    print("3. 运行 python examples/basic_usage.py 查看基本使用")
    print("4. 运行 python examples/api_server_example.py 启动API服务器")

if __name__ == "__main__":
    main()
