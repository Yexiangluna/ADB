"""
ADB 测试套件
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from adb import ADB, ADBError, ValidationError, TableNotFoundError

class TestADB(unittest.TestCase):
    """ADB核心功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db.json")
        self.db = ADB(db_path=self.db_path, enable_logging=False)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_create_table(self):
        """测试创建表"""
        # 测试创建表
        self.assertTrue(self.db.create_table("users"))
        self.assertIn("users", self.db.list_tables())
        
        # 测试重复创建
        self.assertFalse(self.db.create_table("users"))
    
    def test_create_table_with_schema(self):
        """测试带结构创建表"""
        schema = {
            'name': {'type': str, 'required': True, 'max_length': 50},
            'age': {'type': int, 'required': True}
        }
        self.assertTrue(self.db.create_table("users", schema))
        self.assertEqual(self.db.get_schema("users"), schema)
    
    def test_insert_and_select(self):
        """测试插入和查询"""
        self.db.create_table("users")
        
        # 测试插入
        record = {"name": "张三", "age": 25}
        self.assertTrue(self.db.insert("users", record))
        
        # 测试查询
        records = self.db.select("users")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "张三")
        self.assertIn("_id", records[0])
        self.assertIn("_created_at", records[0])
    
    def test_validation(self):
        """测试数据验证"""
        schema = {
            'name': {'type': str, 'required': True, 'max_length': 10},
            'age': {'type': int, 'required': True}
        }
        self.db.create_table("users", schema)
        
        # 测试必填字段验证
        with self.assertRaises(ValidationError):
            self.db.insert("users", {"age": 25})  # 缺少name
        
        # 测试类型验证
        with self.assertRaises(ValidationError):
            self.db.insert("users", {"name": "张三", "age": "invalid"})
        
        # 测试长度验证
        with self.assertRaises(ValidationError):
            self.db.insert("users", {"name": "a" * 11, "age": 25})
    
    def test_update_and_delete(self):
        """测试更新和删除"""
        self.db.create_table("users")
        self.db.insert("users", {"name": "张三", "age": 25})
        self.db.insert("users", {"name": "李四", "age": 30})
        
        # 测试更新
        count = self.db.update("users", {"name": "张三"}, {"age": 26})
        self.assertEqual(count, 1)
        
        # 验证更新结果
        records = self.db.select("users", {"name": "张三"})
        self.assertEqual(records[0]["age"], 26)
        
        # 测试删除
        count = self.db.delete("users", {"name": "李四"})
        self.assertEqual(count, 1)
        self.assertEqual(len(self.db.select("users")), 1)
    
    def test_transaction(self):
        """测试事务"""
        self.db.create_table("users")
        
        # 测试成功事务
        with self.db.transaction():
            self.db.insert("users", {"name": "张三", "age": 25})
            self.db.insert("users", {"name": "李四", "age": 30})
        
        self.assertEqual(len(self.db.select("users")), 2)
        
        # 测试失败事务（回滚）
        try:
            with self.db.transaction():
                self.db.insert("users", {"name": "王五", "age": 35})
                raise Exception("模拟错误")
        except:
            pass
        
        # 应该回滚，仍然是2条记录
        self.assertEqual(len(self.db.select("users")), 2)
    
    def test_indexes(self):
        """测试索引功能"""
        self.db.create_table("users")
        self.db.insert("users", {"name": "张三", "age": 25})
        self.db.insert("users", {"name": "李四", "age": 30})
        
        # 创建索引
        self.assertTrue(self.db.create_index("users", "name"))
        self.assertIn("name", self.db.list_indexes("users"))
        
        # 测试索引查询
        records = self.db.select("users", {"name": "张三"})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["name"], "张三")
    
    def test_aggregation(self):
        """测试聚合查询"""
        self.db.create_table("sales")
        self.db.insert("sales", {"product": "A", "amount": 100})
        self.db.insert("sales", {"product": "B", "amount": 200})
        self.db.insert("sales", {"product": "A", "amount": 150})
        
        # 测试分组聚合
        pipeline = [{"$group": {"_id": "product"}}]
        result = self.db.aggregate("sales", pipeline)
        
        self.assertEqual(len(result), 2)
        products = [r["_id"] for r in result]
        self.assertIn("A", products)
        self.assertIn("B", products)
    
    def test_backup_restore(self):
        """测试备份和恢复"""
        self.db.create_table("users")
        self.db.insert("users", {"name": "张三", "age": 25})
        
        # 测试备份
        backup_path = os.path.join(self.temp_dir, "backup.json")
        self.assertTrue(self.db.backup(backup_path))
        self.assertTrue(os.path.exists(backup_path))
        
        # 修改数据
        self.db.insert("users", {"name": "李四", "age": 30})
        self.assertEqual(len(self.db.select("users")), 2)
        
        # 测试恢复
        self.assertTrue(self.db.restore(backup_path))
        self.assertEqual(len(self.db.select("users")), 1)
    
    def test_table_operations(self):
        """测试表操作"""
        # 创建表
        self.db.create_table("test_table")
        self.db.insert("test_table", {"data": "test"})
        
        # 重命名表
        self.assertTrue(self.db.rename_table("test_table", "renamed_table"))
        self.assertIn("renamed_table", self.db.list_tables())
        self.assertNotIn("test_table", self.db.list_tables())
        
        # 清空表
        self.assertTrue(self.db.truncate_table("renamed_table"))
        self.assertEqual(len(self.db.select("renamed_table")), 0)
        
        # 删除表
        self.assertTrue(self.db.drop_table("renamed_table"))
        self.assertNotIn("renamed_table", self.db.list_tables())

if __name__ == '__main__':
    unittest.main()
