"""
ADB API 测试套件
"""

import unittest
import tempfile
import shutil
import json
import os
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from adb import ADB, ADBAPIServer
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

@unittest.skipIf(not FLASK_AVAILABLE, "Flask未安装")
class TestADBAPI(unittest.TestCase):
    """ADB API测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_api_db.json")
        self.db = ADB(db_path=self.db_path, enable_logging=False)
        self.api_server = ADBAPIServer(self.db, api_key="test-key")
        self.app = self.api_server.app.test_client()
        self.headers = {'X-API-Key': 'test-key', 'Content-Type': 'application/json'}
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir)
    
    def test_health_check(self):
        """测试健康检查"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_api_key_validation(self):
        """测试API密钥验证"""
        # 无密钥请求
        response = self.app.get('/api/tables')
        self.assertEqual(response.status_code, 401)
        
        # 错误密钥
        response = self.app.get('/api/tables', headers={'X-API-Key': 'wrong-key'})
        self.assertEqual(response.status_code, 401)
        
        # 正确密钥
        response = self.app.get('/api/tables', headers=self.headers)
        self.assertEqual(response.status_code, 200)
    
    def test_table_management(self):
        """测试表管理API"""
        # 创建表
        data = {'name': 'users', 'schema': {'name': {'type': 'str', 'required': True}}}
        response = self.app.post('/api/tables', 
                               data=json.dumps(data), 
                               headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # 列出表
        response = self.app.get('/api/tables', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('users', data['tables'])
        
        # 删除表
        response = self.app.delete('/api/tables/users', headers=self.headers)
        self.assertEqual(response.status_code, 200)
    
    def test_record_operations(self):
        """测试记录操作API"""
        # 创建表
        self.db.create_table("users")
        
        # 插入记录
        data = {'record': {'name': '张三', 'age': 25}}
        response = self.app.post('/api/tables/users/records',
                               data=json.dumps(data),
                               headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # 查询记录
        response = self.app.get('/api/tables/users/records', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data['records']), 1)
        self.assertEqual(data['records'][0]['name'], '张三')
        
        # 更新记录
        update_data = {'condition': {'name': '张三'}, 'values': {'age': 26}}
        response = self.app.put('/api/tables/users/records',
                              data=json.dumps(update_data),
                              headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # 删除记录
        delete_data = {'condition': {'name': '张三'}}
        response = self.app.delete('/api/tables/users/records',
                                 data=json.dumps(delete_data),
                                 headers=self.headers)
        self.assertEqual(response.status_code, 200)
    
    def test_batch_operations(self):
        """测试批量操作"""
        self.db.create_table("products")
        
        # 批量插入
        data = {'record': [
            {'name': '产品1', 'price': 100},
            {'name': '产品2', 'price': 200}
        ]}
        response = self.app.post('/api/tables/products/records',
                               data=json.dumps(data),
                               headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['success_count'], 2)

if __name__ == '__main__':
    unittest.main()
