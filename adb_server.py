#!/usr/bin/env python3
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
