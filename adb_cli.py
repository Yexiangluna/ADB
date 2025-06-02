#!/usr/bin/env python3
"""
ADB 命令行接口
"""

import sys
import argparse
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from adb import ADB, ADBError

def show_interactive_menu(parser):
    """显示交互式菜单"""
    print("\n" + "="*50)
    print("🎯 ADB 数据库管理系统")
    print("="*50)
    print("\n欢迎使用 ADB！这是一个轻量级的数据库管理工具。")
    print("\n可用的命令：")
    print("  1. create-table  - 创建数据表")
    print("  2. list-tables   - 列出所有表") 
    print("  3. insert        - 插入数据")
    print("  4. select        - 查询数据")
    print("  5. backup        - 备份数据库")
    print("  6. help          - 显示详细帮助")
    print("  7. exit          - 退出程序")
    
    while True:
        print("\n" + "-"*30)
        choice = input("请选择操作 (1-7) 或输入命令名: ").strip().lower()
        
        if choice in ['7', 'exit', 'quit', 'q']:
            print("👋 感谢使用 ADB！")
            break
        elif choice in ['6', 'help', 'h']:
            parser.print_help()
        elif choice in ['1', 'create-table']:
            interactive_create_table()
        elif choice in ['2', 'list-tables']:
            interactive_list_tables()
        elif choice in ['3', 'insert']:
            interactive_insert()
        elif choice in ['4', 'select']:
            interactive_select()
        elif choice in ['5', 'backup']:
            interactive_backup()
        else:
            print("❌ 无效选择，请重新输入。")
        
        # 询问是否继续
        if choice not in ['6', 'help', 'h']:
            continue_choice = input("\n按回车键继续，或输入 'q' 退出: ").strip().lower()
            if continue_choice in ['q', 'quit', 'exit']:
                print("👋 感谢使用 ADB！")
                break

def interactive_create_table():
    """交互式创建表"""
    try:
        db_path = input("数据库文件路径 (回车使用默认 'adb_data.json'): ").strip() or "adb_data.json"
        table_name = input("请输入表名: ").strip()
        
        if not table_name:
            print("❌ 表名不能为空")
            return
            
        db = ADB(db_path, enable_logging=True)
        success = db.create_table(table_name)
        
        if success:
            print(f"✅ 表 '{table_name}' 创建成功！")
        else:
            print(f"⚠️ 表 '{table_name}' 已存在")
            
    except Exception as e:
        print(f"❌ 创建表失败: {e}")

def interactive_list_tables():
    """交互式列出表"""
    try:
        db_path = input("数据库文件路径 (回车使用默认 'adb_data.json'): ").strip() or "adb_data.json"
        db = ADB(db_path, enable_logging=True)
        tables = db.list_tables()
        
        if not tables:
            print("📭 数据库中没有表")
        else:
            print(f"\n📊 数据库中的表 (共 {len(tables)} 个):")
            for table in tables:
                info = db.get_table_info(table)
                print(f"  📋 {table} ({info['record_count']} 条记录)")
                
    except Exception as e:
        print(f"❌ 列出表失败: {e}")

def interactive_insert():
    """交互式插入数据"""
    try:
        db_path = input("数据库文件路径 (回车使用默认 'adb_data.json'): ").strip() or "adb_data.json"
        table_name = input("请输入表名: ").strip()
        
        if not table_name:
            print("❌ 表名不能为空")
            return
            
        print("\n请输入数据 (JSON格式):")
        print("示例: {\"name\":\"张三\",\"age\":25,\"email\":\"zhangsan@example.com\"}")
        data_str = input("数据: ").strip()
        
        if not data_str:
            print("❌ 数据不能为空")
            return
            
        import json
        data = json.loads(data_str)
        
        db = ADB(db_path, enable_logging=True)
        success = db.insert(table_name, data)
        
        if success:
            print("✅ 数据插入成功！")
        else:
            print("❌ 数据插入失败")
            
    except json.JSONDecodeError:
        print("❌ JSON格式错误，请检查数据格式")
    except Exception as e:
        print(f"❌ 插入数据失败: {e}")

def interactive_select():
    """交互式查询数据"""
    try:
        db_path = input("数据库文件路径 (回车使用默认 'adb_data.json'): ").strip() or "adb_data.json"
        table_name = input("请输入表名: ").strip()
        
        if not table_name:
            print("❌ 表名不能为空")
            return
            
        limit_str = input("限制结果数量 (回车显示所有): ").strip()
        limit = int(limit_str) if limit_str else None
        
        db = ADB(db_path, enable_logging=True)
        records = db.select(table_name, limit=limit)
        
        print(f"\n📋 查询结果 (共 {len(records)} 条记录):")
        if records:
            import json
            print(json.dumps(records, ensure_ascii=False, indent=2))
        else:
            print("📭 没有找到数据")
            
    except Exception as e:
        print(f"❌ 查询数据失败: {e}")

def interactive_backup():
    """交互式备份数据库"""
    try:
        db_path = input("数据库文件路径 (回车使用默认 'adb_data.json'): ").strip() or "adb_data.json"
        backup_path = input("备份文件路径 (回车自动生成): ").strip() or None
        
        db = ADB(db_path, enable_logging=True)
        success = db.backup(backup_path)
        
        if success:
            print("✅ 数据库备份成功！")
        else:
            print("❌ 数据库备份失败")
            
    except Exception as e:
        print(f"❌ 备份失败: {e}")

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
        # 如果没有命令参数，显示交互式界面
        show_interactive_menu(parser)
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
