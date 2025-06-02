"""
ADB 基本使用示例
"""

from adb import ADB, ADBError, ValidationError

def main():
    """基本使用示例"""
    print("=== ADB 基本使用示例 ===\n")
    
    # 1. 创建数据库实例
    print("1. 创建数据库实例")
    db = ADB("example_database.json", enable_logging=True)
    print(f"数据库路径: {db.db_path}")
    print()
    
    # 2. 创建表（带验证）
    print("2. 创建用户表")
    user_schema = {
        'name': {'type': str, 'required': True, 'max_length': 50},
        'email': {'type': str, 'required': True, 'max_length': 100},
        'age': {'type': int, 'required': False},
        'department': {'type': str, 'required': False, 'max_length': 30}
    }
    
    if db.create_table("users", user_schema):
        print("✅ 用户表创建成功")
    else:
        print("ℹ️ 用户表已存在")
    print()
    
    # 3. 插入数据
    print("3. 插入用户数据")
    users_data = [
        {"name": "张三", "email": "zhangsan@example.com", "age": 28, "department": "技术部"},
        {"name": "李四", "email": "lisi@example.com", "age": 32, "department": "销售部"},
        {"name": "王五", "email": "wangwu@example.com", "age": 25, "department": "技术部"},
        {"name": "赵六", "email": "zhaoliu@example.com", "age": 30, "department": "人事部"}
    ]
    
    for user in users_data:
        try:
            db.insert("users", user)
            print(f"✅ 插入用户: {user['name']}")
        except ValidationError as e:
            print(f"❌ 插入失败: {e}")
    print()
    
    # 4. 创建索引提高查询性能
    print("4. 创建索引")
    db.create_index("users", "department")
    db.create_index("users", "age")
    print("✅ 为 department 和 age 字段创建索引")
    print()
    
    # 5. 查询数据
    print("5. 查询数据")
    
    # 查询所有用户
    all_users = db.select("users")
    print(f"所有用户 ({len(all_users)} 人):")
    for user in all_users:
        print(f"  - {user['name']} ({user['age']}岁) - {user['department']}")
    print()
    
    # 条件查询
    tech_users = db.select("users", {"department": "技术部"})
    print(f"技术部用户 ({len(tech_users)} 人):")
    for user in tech_users:
        print(f"  - {user['name']} ({user['age']}岁)")
    print()
    
    # 范围查询
    young_users = db.select("users", {"age": {"$lt": 30}})
    print(f"30岁以下用户 ({len(young_users)} 人):")
    for user in young_users:
        print(f"  - {user['name']} ({user['age']}岁)")
    print()
    
    # 6. 聚合查询
    print("6. 聚合查询")
    pipeline = [{"$group": {"_id": "department"}}]
    dept_stats = db.aggregate("users", pipeline)
    print("各部门人数统计:")
    for stat in dept_stats:
        print(f"  - {stat['_id']}: {stat['count']} 人")
    print()
    
    # 7. 更新数据
    print("7. 更新数据")
    updated_count = db.update("users", {"name": "张三"}, {"age": 29})
    print(f"✅ 更新了 {updated_count} 条记录")
    print()
    
    # 8. 事务操作
    print("8. 事务操作示例")
    try:
        with db.transaction():
            # 在事务中进行多个操作
            db.insert("users", {"name": "新用户1", "email": "new1@example.com", "department": "测试部"})
            db.insert("users", {"name": "新用户2", "email": "new2@example.com", "department": "测试部"})
            db.update("users", {"name": "李四"}, {"department": "市场部"})
            print("✅ 事务操作完成")
    except Exception as e:
        print(f"❌ 事务失败: {e}")
    print()
    
    # 9. 表信息和统计
    print("9. 表信息")
    table_info = db.get_table_info("users")
    print(f"表名: {table_info['name']}")
    print(f"记录数: {table_info['record_count']}")
    print(f"索引数: {len(table_info['indexes'])}")
    print(f"数据大小: {table_info['size_bytes']} 字节")
    print()
    
    # 10. 备份
    print("10. 数据备份")
    backup_success = db.backup("users_backup.json")
    if backup_success:
        print("✅ 数据备份成功")
    else:
        print("❌ 数据备份失败")
    print()
    
    print("=== 示例完成 ===")

if __name__ == "__main__":
    main()
