"""
ADB (API Database) - 简单的基于API的数据库管理系统

主要功能：
1. 基础CRUD操作(创建、读取、更新、删除)
2. 表结构管理和数据验证
3. 索引支持以提高查询性能
4. 事务处理确保数据一致性
5. 增强查询功能（范围查询、模糊匹配、分页）
6. 聚合查询支持
7. 数据备份和恢复
8. 错误处理和日志记录

存储方式:JSON文件
使用场景：小型应用、原型开发、测试环境
"""

import json
import os
import shutil
import logging
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

# 添加Flask API支持
try:
    from flask import Flask, request, jsonify
    from functools import wraps
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("警告: Flask未安装，API服务器功能不可用。运行 'pip install flask' 安装。")

# 添加配置支持
try:
    from config import config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("警告: 配置模块未找到，使用默认配置")

# 添加环境变量支持
try:
    from dotenv import load_dotenv
    load_dotenv()  # 加载 .env 文件
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

class ADBError(Exception):
    """ADB自定义异常"""
    def __init__(self, message: str, error_code: str = None):
        super().__init__(message)
        self.error_code = error_code
        self.timestamp = datetime.now().isoformat()

class ValidationError(ADBError):
    """数据验证错误"""
    pass

class TableNotFoundError(ADBError):
    """表不存在错误"""
    pass

class ADB:
    """
    简单的基于API的数据库管理系统
    
    核心特性：
    - 表管理：创建/删除表，定义表结构
    - 数据操作：插入、查询、更新、删除记录
    - 索引系统：提高查询性能
    - 事务支持：保证数据一致性
    - 增强查询：支持范围查询、模糊匹配、分页
    - 聚合功能：基本的数据分析
    - 备份恢复：数据安全保障
    """
    
    def __init__(self, db_path: str = None, enable_logging: bool = None):
        """
        初始化ADB实例
        
        Args:
            db_path: 数据库文件路径（可选，从配置读取）
            enable_logging: 是否启用日志记录（可选，从配置读取）
        """
        # 使用配置系统
        if CONFIG_AVAILABLE:
            config.create_directories()  # 创建必要目录
            self.db_path = Path(db_path or config.get('database.path', "adb_data.json"))
            enable_logging = enable_logging if enable_logging is not None else config.get('logging.level') != 'CRITICAL'
            self.max_records = config.get('database.max_records_per_table', 100000)
        else:
            self.db_path = Path(db_path or "adb_data.json")
            enable_logging = enable_logging if enable_logging is not None else False
            self.max_records = 100000
        
        self.data = {}              # 存储所有表数据
        self.indexes = {}           # 存储索引信息
        self.schemas = {}           # 存储表结构定义
        self._transaction_active = False     # 事务状态
        self._transaction_backup = None      # 事务备份数据
        self._last_save_time = 0    # 最后保存时间
        self._save_interval = 1     # 保存间隔（秒）
        
        # 配置日志
        if enable_logging and CONFIG_AVAILABLE:
            self._setup_logging()
        elif enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        self.logger = logging.getLogger(__name__)
        self.load_database()
    
    def _setup_logging(self):
        """设置详细的日志配置"""
        if not CONFIG_AVAILABLE:
            return
            
        log_level = getattr(logging, config.get('logging.level', 'INFO'))
        log_format = config.get('logging.format')
        log_file = config.get('logging.file')
        
        # 创建日志目录
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8') if log_file else logging.StreamHandler(),
                logging.StreamHandler()
            ]
        )
    
    def _validate_table_name(self, table_name: str) -> None:
        """验证表名有效性"""
        if not table_name or not isinstance(table_name, str):
            raise ValidationError("表名必须是非空字符串")
        if len(table_name) > 64:
            raise ValidationError("表名长度不能超过64个字符")
        if not table_name.replace('_', '').replace('-', '').isalnum():
            raise ValidationError("表名只能包含字母、数字、下划线和连字符")
    
    def _check_table_exists(self, table_name: str) -> None:
        """检查表是否存在"""
        if table_name not in self.data:
            raise TableNotFoundError(f"表 '{table_name}' 不存在")
    
    def _check_record_limit(self, table_name: str) -> None:
        """检查记录数量限制"""
        if len(self.data[table_name]) >= self.max_records:
            raise ADBError(f"表 '{table_name}' 已达到最大记录数限制 ({self.max_records})")
    
    def load_database(self) -> None:
        """加载数据库文件"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # 兼容旧格式和新格式
                    if isinstance(content, dict) and 'tables' in content:
                        self.data = content.get('tables', {})
                        self.schemas = content.get('schemas', {})
                        self.indexes = content.get('indexes', {})
                    else:
                        self.data = content
                        self.schemas = {}
                        self.indexes = {}
                self.logger.info(f"数据库加载成功: {len(self.data)} 个表")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"数据库加载失败: {e}")
                self.data = {}
                self.schemas = {}
                self.indexes = {}
        else:
            self.data = {}
            self.schemas = {}
            self.indexes = {}
    
    def save_database(self) -> bool:
        """保存数据库到文件（带频率限制）"""
        current_time = time.time()
        if current_time - self._last_save_time < self._save_interval and not self._transaction_active:
            return True  # 跳过过于频繁的保存
        
        try:
            # 确保目录存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 新格式保存，包含元数据
            content = {
                'version': '1.0',
                'created_at': datetime.now().isoformat(),
                'tables': self.data,
                'schemas': self.schemas,
                'indexes': self.indexes
            }
            
            # 原子写入
            temp_path = self.db_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            
            temp_path.replace(self.db_path)
            self._last_save_time = current_time
            return True
        except IOError as e:
            self.logger.error(f"数据库保存失败: {e}")
            return False
    
    def create_table(self, table_name: str, schema: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建表
        
        Args:
            table_name: 表名
            schema: 表结构定义，包含字段类型和约束
                   例：{'name': {'type': str, 'required': True}}
        
        Returns:
            bool: 创建成功返回True，表已存在返回False
        """
        self._validate_table_name(table_name)
        
        if table_name in self.data:
            return False
            
        self.data[table_name] = []
        self.indexes[table_name] = {}
        if schema:
            self.schemas[table_name] = schema
            
        self.logger.info(f"创建表: {table_name}")
        return self.save_database()
    
    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        self._check_table_exists(table_name)
        
        del self.data[table_name]
        # 清理相关索引和结构
        self.indexes.pop(table_name, None)
        self.schemas.pop(table_name, None)
        
        self.logger.info(f"删除表: {table_name}")
        return self.save_database()
    
    def _validate_record(self, table_name: str, record: Dict[str, Any]) -> bool:
        """验证记录是否符合表结构"""
        if table_name not in self.schemas:
            return True
        
        schema = self.schemas[table_name]
        for field, constraints in schema.items():
            if constraints.get('required', False) and field not in record:
                raise ValidationError(f"必填字段 '{field}' 缺失")
            
            if field in record:
                value = record[field]
                field_type = constraints.get('type')
                if field_type and not isinstance(value, field_type):
                    raise ValidationError(f"字段 '{field}' 类型错误，期望 {field_type.__name__}")
                
                # 检查字符串长度限制
                max_length = constraints.get('max_length')
                if max_length and isinstance(value, str) and len(value) > max_length:
                    raise ValidationError(f"字段 '{field}' 长度超过限制 ({max_length})")
        
        return True
    
    def insert(self, table_name: str, record: Dict[str, Any]) -> bool:
        """
        插入记录到表中
        
        功能：
        - 数据验证（根据表结构）
        - 自动添加时间戳和ID
        - 更新相关索引
        
        Args:
            table_name: 表名
            record: 要插入的记录数据
            
        Returns:
            bool: 插入成功返回True
        """
        self._check_table_exists(table_name)
        self._check_record_limit(table_name)
        
        # 验证记录
        record_copy = record.copy()  # 避免修改原始数据
        self._validate_record(table_name, record_copy)
        
        # 添加时间戳和ID
        record_copy['_created_at'] = datetime.now().isoformat()
        record_copy['_id'] = len(self.data[table_name]) + 1
        
        # 更新索引
        self._update_indexes_for_insert(table_name, record_copy, len(self.data[table_name]))
        
        self.data[table_name].append(record_copy)
        return self.save_database()
    
    def _update_indexes_for_insert(self, table_name: str, record: Dict[str, Any], record_index: int) -> None:
        """为插入操作更新索引"""
        if table_name in self.indexes:
            for column, index in self.indexes[table_name].items():
                if column in record:
                    value = record[column]
                    if value not in index:
                        index[value] = []
                    index[value].append(record_index)
    
    def select(self, table_name: str, condition: Optional[Dict[str, Any]] = None, 
               limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        增强的查询功能
        
        支持的查询条件：
        - 精确匹配：{'name': '张三'}
        - 范围查询：{'age': {'$gt': 18, '$lt': 60}}
        - 模糊匹配：{'name': {'$like': '张'}}
        - 分页查询：limit和offset参数
        
        Args:
            table_name: 表名
            condition: 查询条件
            limit: 限制返回记录数
            offset: 跳过记录数（用于分页）
            
        Returns:
            List[Dict]: 匹配的记录列表
        """
        if table_name not in self.data:
            return []
        
        records = self.data[table_name]
        
        if condition is None:
            result = records[offset:offset + limit if limit else None]
            return result
        
        # 尝试使用索引优化查询
        if len(condition) == 1 and table_name in self.indexes:
            key, value = next(iter(condition.items()))
            if key in self.indexes[table_name] and not isinstance(value, dict):
                # 使用索引查询
                indexes = self.indexes[table_name][key].get(value, [])
                result = [records[i] for i in indexes if i < len(records)]
                return result[offset:offset + limit if limit else None]
        
        # 普通查询
        result = []
        for record in records:
            if self._match_condition(record, condition):
                result.append(record)
        
        return result[offset:offset + limit if limit else None]
    
    def _match_condition(self, record: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """检查记录是否匹配条件"""
        for key, value in condition.items():
            if isinstance(value, dict):
                # 支持范围查询
                if '$gt' in value and key in record and record[key] <= value['$gt']:
                    return False
                if '$lt' in value and key in record and record[key] >= value['$lt']:
                    return False
                if '$gte' in value and key in record and record[key] < value['$gte']:
                    return False
                if '$lte' in value and key in record and record[key] > value['$lte']:
                    return False
                if '$like' in value and key in record:
                    if value['$like'].lower() not in str(record[key]).lower():
                        return False
            else:
                if key not in record or record[key] != value:
                    return False
        return True
    
    @contextmanager
    def transaction(self):
        """
        事务上下文管理器
        
        使用方式：
        with db.transaction():
            db.insert("users", data1)
            db.update("users", condition, data2)
        # 如果出现异常，自动回滚
        """
        if self._transaction_active:
            raise ADBError("已有活跃事务")
        
        self._transaction_active = True
        self._transaction_backup = json.dumps(self.data)
        
        try:
            yield
            self.save_database()
        except Exception:
            # 回滚
            self.data = json.loads(self._transaction_backup)
            raise
        finally:
            self._transaction_active = False
            self._transaction_backup = None
    
    def backup(self, backup_path: Optional[str] = None) -> bool:
        """
        备份数据库文件
        
        Args:
            backup_path: 备份文件路径，默认自动生成时间戳文件名
            
        Returns:
            bool: 备份成功返回True
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            self.logger.info(f"数据库已备份到: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"备份失败: {e}")
            return False
    
    def restore(self, backup_path: str) -> bool:
        """从备份恢复数据库"""
        try:
            shutil.copy2(backup_path, self.db_path)
            self.load_database()
            self.logger.info(f"已从备份恢复: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"恢复失败: {e}")
            return False
    
    def aggregate(self, table_name: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        聚合查询功能
        
        支持的聚合操作：
        - $group: 分组统计
        - $match: 过滤条件
        
        例：按年龄分组统计
        pipeline = [{"$group": {"_id": "age"}}]
        
        Args:
            table_name: 表名
            pipeline: 聚合管道操作列表
            
        Returns:
            List[Dict]: 聚合结果
        """
        if table_name not in self.data:
            return []
        
        records = self.data[table_name]
        
        for stage in pipeline:
            if '$group' in stage:
                # 分组聚合
                group_key = stage['$group']['_id']
                result = {}
                
                for record in records:
                    key = record.get(group_key, 'null')
                    if key not in result:
                        result[key] = {'_id': key, 'count': 0}
                    result[key]['count'] += 1
                
                records = list(result.values())
            
            elif '$match' in stage:
                # 过滤
                condition = stage['$match']
                records = [r for r in records if self._match_condition(r, condition)]
        
        return records
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表的元数据信息
        
        返回信息包括：
        - 表名
        - 记录数量
        - 表结构定义
        - 索引列表
        - 存储大小
        
        Args:
            table_name: 表名
            
        Returns:
            Dict: 表信息字典
        """
        if table_name not in self.data:
            return {}
        
        return {
            'name': table_name,
            'record_count': len(self.data[table_name]),
            'schema': self.schemas.get(table_name, {}),
            'indexes': list(self.indexes.get(table_name, {}).keys()),
            'size_bytes': len(json.dumps(self.data[table_name]).encode('utf-8'))
        }
    
    def drop_table(self, table_name: str) -> bool:
        """删除表"""
        if table_name not in self.data:
            return False
        del self.data[table_name]
        # 清理相关索引和结构
        if table_name in self.indexes:
            del self.indexes[table_name]
        if table_name in self.schemas:
            del self.schemas[table_name]
        return self.save_database()
    
    def update(self, table_name: str, condition: Dict[str, Any], new_values: Dict[str, Any]) -> int:
        """更新记录"""
        self._check_table_exists(table_name)
        
        if not condition:
            raise ValidationError("更新操作必须提供条件")
        
        updated_count = 0
        for record in self.data[table_name]:
            if self._match_condition(record, condition):
                # 验证更新数据
                temp_record = record.copy()
                temp_record.update(new_values)
                self._validate_record(table_name, temp_record)
                
                # 执行更新
                record.update(new_values)
                record['_updated_at'] = datetime.now().isoformat()
                updated_count += 1
        
        if updated_count > 0:
            # 重建相关索引
            self._rebuild_indexes(table_name)
            self.save_database()
            self.logger.info(f"更新表 {table_name}: {updated_count} 条记录")
        
        return updated_count
    
    def delete(self, table_name: str, condition: Dict[str, Any]) -> int:
        """删除记录"""
        self._check_table_exists(table_name)
        
        if not condition:
            raise ValidationError("删除操作必须提供条件")
        
        original_count = len(self.data[table_name])
        
        # 保留不匹配条件的记录
        self.data[table_name] = [
            record for record in self.data[table_name]
            if not self._match_condition(record, condition)
        ]
        
        deleted_count = original_count - len(self.data[table_name])
        
        if deleted_count > 0:
            # 重建索引
            self._rebuild_indexes(table_name)
            self.save_database()
            self.logger.info(f"从表 {table_name} 删除 {deleted_count} 条记录")
        
        return deleted_count
    
    def list_tables(self) -> List[str]:
        """列出所有表名"""
        return list(self.data.keys())
    
    def count(self, table_name: str, condition: Optional[Dict[str, Any]] = None) -> int:
        """统计表中记录数"""
        if table_name not in self.data:
            return 0
        
        if condition is None:
            return len(self.data[table_name])
        
        # 条件统计
        count = 0
        for record in self.data[table_name]:
            if self._match_condition(record, condition):
                count += 1
        return count
    
    def _rebuild_indexes(self, table_name: str) -> None:
        """重建表的所有索引"""
        if table_name not in self.indexes:
            return
        
        for column in list(self.indexes[table_name].keys()):
            self.create_index(table_name, column)
    
    def drop_index(self, table_name: str, column: str) -> bool:
        """删除索引"""
        if (table_name not in self.indexes or 
            column not in self.indexes[table_name]):
            return False
        
        del self.indexes[table_name][column]
        return True
    
    def execute_sql_like(self, query: str) -> Any:
        """
        执行类SQL查询（简化版）
        支持基本的SELECT, INSERT, UPDATE, DELETE语句
        """
        query = query.strip().upper()
        
        if query.startswith('SELECT COUNT(*) FROM'):
            table_name = query.split('FROM')[1].strip()
            return self.count(table_name)
        
        elif query.startswith('SHOW TABLES'):
            return self.list_tables()
        
        # 可以继续扩展更多SQL语法支持
        else:
            raise ADBError(f"不支持的查询语句: {query}")

    def alter_table(self, table_name: str, action: str, **kwargs) -> bool:
        """
        修改表结构
        
        Args:
            table_name: 表名
            action: 操作类型 ('add_column', 'drop_column', 'modify_column')
            **kwargs: 操作参数
            
        Returns:
            bool: 操作成功返回True
        """
        if table_name not in self.data:
            return False
            
        if action == 'add_column':
            column_name = kwargs.get('column_name')
            column_def = kwargs.get('column_def', {})
            default_value = kwargs.get('default_value')
            
            if table_name in self.schemas:
                self.schemas[table_name][column_name] = column_def
            
            # 为现有记录添加默认值
            for record in self.data[table_name]:
                if column_name not in record:
                    record[column_name] = default_value
                    
        elif action == 'drop_column':
            column_name = kwargs.get('column_name')
            
            if table_name in self.schemas and column_name in self.schemas[table_name]:
                del self.schemas[table_name][column_name]
            
            # 从所有记录中删除该列
            for record in self.data[table_name]:
                if column_name in record:
                    del record[column_name]
            
            # 删除相关索引
            if table_name in self.indexes and column_name in self.indexes[table_name]:
                del self.indexes[table_name][column_name]
                
        return self.save_database()
    
    def rename_table(self, old_name: str, new_name: str) -> bool:
        """
        重命名表
        
        Args:
            old_name: 原表名
            new_name: 新表名
            
        Returns:
            bool: 重命名成功返回True
        """
        if old_name not in self.data or new_name in self.data:
            return False
            
        # 移动数据
        self.data[new_name] = self.data[old_name]
        del self.data[old_name]
        
        # 移动索引
        if old_name in self.indexes:
            self.indexes[new_name] = self.indexes[old_name]
            del self.indexes[old_name]
            
        # 移动表结构
        if old_name in self.schemas:
            self.schemas[new_name] = self.schemas[old_name]
            del self.schemas[old_name]
            
        return self.save_database()
    
    def truncate_table(self, table_name: str) -> bool:
        """
        清空表数据（保留表结构）
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 操作成功返回True
        """
        if table_name not in self.data:
            return False
            
        self.data[table_name] = []
        
        # 清空索引
        if table_name in self.indexes:
            for column in self.indexes[table_name]:
                self.indexes[table_name][column] = {}
                
        return self.save_database()
    
    def get_schema(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        获取表结构定义
        
        Args:
            table_name: 表名
            
        Returns:
            Dict: 表结构定义，不存在返回None
        """
        return self.schemas.get(table_name)
    
    def set_schema(self, table_name: str, schema: Dict[str, Any]) -> bool:
        """
        设置表结构定义
        
        Args:
            table_name: 表名
            schema: 表结构定义
            
        Returns:
            bool: 设置成功返回True
        """
        if table_name not in self.data:
            return False
            
        self.schemas[table_name] = schema
        return self.save_database()
    
    def analyze_table(self, table_name: str) -> Dict[str, Any]:
        """
        分析表统计信息
        
        Args:
            table_name: 表名
            
        Returns:
            Dict: 表分析结果
        """
        if table_name not in self.data:
            return {}
            
        records = self.data[table_name]
        if not records:
            return {'record_count': 0}
            
        analysis = {
            'record_count': len(records),
            'columns': {},
            'data_types': {},
            'null_counts': {},
            'unique_counts': {}
        }
        
        # 分析每列
        for record in records:
            for column, value in record.items():
                if column not in analysis['columns']:
                    analysis['columns'][column] = True
                    analysis['data_types'][column] = type(value).__name__
                    analysis['null_counts'][column] = 0
                    analysis['unique_counts'][column] = set()
                
                if value is None:
                    analysis['null_counts'][column] += 1
                else:
                    analysis['unique_counts'][column].add(str(value))
        
        # 转换unique_counts为数量
        for column in analysis['unique_counts']:
            analysis['unique_counts'][column] = len(analysis['unique_counts'][column])
            
        return analysis
    
    def optimize_table(self, table_name: str) -> bool:
        """
        优化表（重建索引、整理数据）
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 优化成功返回True
        """
        if table_name not in self.data:
            return False
            
        # 重建所有索引
        self._rebuild_indexes(table_name)
        
        # 重新整理记录ID
        for i, record in enumerate(self.data[table_name]):
            record['_id'] = i + 1
            
        return self.save_database()
    
    def explain_query(self, table_name: str, condition: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        查询执行计划分析
        
        Args:
            table_name: 表名
            condition: 查询条件
            
        Returns:
            Dict: 执行计划信息
        """
        plan = {
            'table': table_name,
            'scan_type': 'full_scan',
            'estimated_rows': 0,
            'indexes_used': [],
            'condition': condition
        }
        
        if table_name not in self.data:
            return plan
            
        plan['estimated_rows'] = len(self.data[table_name])
        
        # 检查是否可以使用索引
        if condition and table_name in self.indexes:
            for key in condition.keys():
                if key in self.indexes[table_name]:
                    plan['scan_type'] = 'index_scan'
                    plan['indexes_used'].append(key)
                    
                    # 估算索引扫描行数
                    if not isinstance(condition[key], dict):
                        index_values = self.indexes[table_name][key].get(condition[key], [])
                        plan['estimated_rows'] = len(index_values)
                    
        return plan
    
    def vacuum(self) -> bool:
        """
        数据库维护操作（清理、压缩）
        
        Returns:
            bool: 操作成功返回True
        """
        try:
            # 重建所有表的索引
            for table_name in self.data.keys():
                self.optimize_table(table_name)
                
            # 保存并重新加载数据库文件以压缩
            self.save_database()
            self.load_database()
            
            self.logger.info("数据库维护完成")
            return True
        except Exception as e:
            self.logger.error(f"数据库维护失败: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        获取数据库整体信息
        
        Returns:
            Dict: 数据库信息
        """
        info = {
            'database_path': str(self.db_path),
            'table_count': len(self.data),
            'total_records': sum(len(table_data) for table_data in self.data.values()),
            'total_indexes': sum(len(table_indexes) for table_indexes in self.indexes.values()),
            'tables': {}
        }
        
        # 添加每个表的信息
        for table_name in self.data.keys():
            info['tables'][table_name] = self.get_table_info(table_name)
            
        # 文件大小
        if os.path.exists(self.db_path):
            info['file_size_bytes'] = os.path.getsize(self.db_path)
            
        return info
    
    def import_data(self, table_name: str, data: List[Dict[str, Any]], 
                   mode: str = 'insert') -> Dict[str, int]:
        """
        批量导入数据
        
        Args:
            table_name: 表名
            data: 要导入的数据列表
            mode: 导入模式 ('insert', 'replace', 'update')
            
        Returns:
            Dict: 导入结果统计
        """
        if table_name not in self.data:
            return {'error': 'Table not found', 'imported': 0}
            
        result = {'imported': 0, 'skipped': 0, 'errors': 0}
        
        try:
            with self.transaction():
                for record in data:
                    try:
                        if mode == 'insert':
                            self.insert(table_name, record)
                            result['imported'] += 1
                        elif mode == 'replace':
                            # 先删除相同ID的记录
                            if '_id' in record:
                                self.delete(table_name, {'_id': record['_id']})
                            self.insert(table_name, record)
                            result['imported'] += 1
                        elif mode == 'update':
                            if '_id' in record:
                                updated = self.update(table_name, {'_id': record['_id']}, record)
                                if updated > 0:
                                    result['imported'] += 1
                                else:
                                    self.insert(table_name, record)
                                    result['imported'] += 1
                            else:
                                self.insert(table_name, record)
                                result['imported'] += 1
                    except Exception as e:
                        result['errors'] += 1
                        self.logger.error(f"导入记录失败: {e}")
                        
        except Exception as e:
            result['transaction_error'] = str(e)
            
        return result
    
    def export_data(self, table_name: str, condition: Optional[Dict[str, Any]] = None,
                   format: str = 'json') -> Union[str, List[Dict[str, Any]]]:
        """
        导出表数据
        
        Args:
            table_name: 表名
            condition: 导出条件
            format: 导出格式 ('json', 'list')
            
        Returns:
            导出的数据
        """
        records = self.select(table_name, condition)
        
        if format == 'json':
            return json.dumps(records, ensure_ascii=False, indent=2)
        else:
            return records
    
    def create_index(self, table_name: str, column: str) -> bool:
        """
        为表的指定列创建索引
        
        Args:
            table_name: 表名
            column: 列名
            
        Returns:
            bool: 创建成功返回True
        """
        self._check_table_exists(table_name)
        
        if table_name not in self.indexes:
            self.indexes[table_name] = {}
        
        if column in self.indexes[table_name]:
            return False  # 索引已存在
        
        # 创建索引
        index = {}
        for i, record in enumerate(self.data[table_name]):
            if column in record:
                value = record[column]
                if value not in index:
                    index[value] = []
                index[value].append(i)
        
        self.indexes[table_name][column] = index
        self.logger.info(f"为表 {table_name} 的列 {column} 创建索引")
        return True
    
    def list_indexes(self, table_name: str) -> List[str]:
        """
        列出表的所有索引
        
        Args:
            table_name: 表名
            
        Returns:
            List[str]: 索引列表
        """
        self._check_table_exists(table_name)
        return list(self.indexes.get(table_name, {}).keys())
    
class ADBAPIServer:
    """
    ADB的Web API服务器
    提供RESTful API接口操作数据库
    """
    
    def __init__(self, adb_instance: ADB, api_key: Optional[str] = None):
        """
        初始化API服务器
        
        Args:
            adb_instance: ADB数据库实例
            api_key: API访问密钥（可选）
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask未安装，无法启动API服务器")
        
        self.db = adb_instance
        
        # 使用配置系统
        if CONFIG_AVAILABLE:
            self.api_key = api_key or config.get('api.api_key')
            self.require_api_key = config.get('api.require_api_key', True)
            self.rate_limit = config.get('api.rate_limiting.enabled', False)
        else:
            self.api_key = api_key
            self.require_api_key = bool(api_key)
            self.rate_limit = False
        
        self.app = Flask(__name__)
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制
        self._request_counts = {}  # 简单的速率限制
        self._setup_routes()
    
    def _require_api_key(self, f):
        """API密钥验证装饰器"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if self.require_api_key and self.api_key:
                provided_key = request.headers.get('X-API-Key')
                if not provided_key or provided_key != self.api_key:
                    return jsonify({'error': 'Invalid or missing API key'}), 401
            
            # 简单的速率限制
            if self.rate_limit:
                client_ip = request.remote_addr
                current_time = time.time()
                if client_ip in self._request_counts:
                    last_time, count = self._request_counts[client_ip]
                    if current_time - last_time < 60:  # 1分钟窗口
                        if count > 60:  # 每分钟最多60次请求
                            return jsonify({'error': 'Rate limit exceeded'}), 429
                        self._request_counts[client_ip] = (last_time, count + 1)
                    else:
                        self._request_counts[client_ip] = (current_time, 1)
                else:
                    self._request_counts[client_ip] = (current_time, 1)
            
            return f(*args, **kwargs)
        return decorated_function
    
    def _handle_api_call(self, operation_func, *args, **kwargs):
        """统一API调用处理"""
        try:
            result = operation_func(*args, **kwargs)
            if isinstance(result, (dict, list)):
                return jsonify(result)
            elif isinstance(result, bool):
                return jsonify({'success': result})
            elif isinstance(result, int):
                return jsonify({'count': result})
            elif isinstance(result, str):
                return result
            else:
                return jsonify({'result': result})
        except ValidationError as e:
            return jsonify({'error': str(e), 'error_type': 'validation'}), 400
        except TableNotFoundError as e:
            return jsonify({'error': str(e), 'error_type': 'not_found'}), 404
        except ADBError as e:
            return jsonify({
                'error': str(e), 
                'error_type': 'database',
                'error_code': getattr(e, 'error_code', None)
            }), 400
        except Exception as e:
            self.db.logger.error(f"API调用异常: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    def _setup_routes(self):
        """设置API路由"""
        
        @self.app.errorhandler(413)
        def request_entity_too_large(error):
            return jsonify({'error': 'Request entity too large'}), 413
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({'error': 'Bad request'}), 400
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'version': '1.0.0',
                'tables_count': len(self.db.list_tables()),
                'database_path': str(self.db.db_path),
                'api_server': 'ADB API Server'
            })
        
        # 表管理路由
        @self.app.route('/api/tables', methods=['GET'])
        @self._require_api_key
        def list_tables():
            return self._handle_api_call(lambda: {'tables': self.db.list_tables()})
        
        @self.app.route('/api/tables', methods=['POST'])
        @self._require_api_key
        def create_table():
            data = request.get_json()
            if not data.get('name'):
                return jsonify({'error': 'Table name is required'}), 400
            
            success = self.db.create_table(data.get('name'), data.get('schema'))
            if success:
                return jsonify({'message': f'Table {data.get("name")} created successfully'})
            else:
                return jsonify({'error': f'Table {data.get("name")} already exists'}), 409
        
        @self.app.route('/api/tables/<table_name>', methods=['DELETE'])
        @self._require_api_key
        def drop_table(table_name):
            success = self.db.drop_table(table_name)
            return jsonify({'message': f'Table {table_name} dropped'}) if success else \
                   jsonify({'error': f'Table {table_name} not found'}), 404
        
        # 记录操作路由
        @self.app.route('/api/tables/<table_name>/records', methods=['POST'])
        @self._require_api_key
        def insert_record(table_name):
            data = request.get_json()
            if not data or 'record' not in data:
                return jsonify({'error': 'Record data is required'}), 400
            
            # 批量插入支持
            records = data.get('record')
            if isinstance(records, list):
                success_count = 0
                errors = []
                for i, record in enumerate(records):
                    try:
                        self.db.insert(table_name, record)
                        success_count += 1
                    except Exception as e:
                        errors.append({'index': i, 'error': str(e)})
                return jsonify({
                    'message': f'Inserted {success_count} records',
                    'success_count': success_count,
                    'errors': errors
                })
            else:
                return self._handle_api_call(self.db.insert, table_name, records)
        
        @self.app.route('/api/tables/<table_name>/records', methods=['GET'])
        @self._require_api_key
        def select_records(table_name):
            try:
                condition = None
                condition_str = request.args.get('condition')
                if condition_str:
                    condition = json.loads(condition_str)
                
                limit = request.args.get('limit', type=int)
                offset = request.args.get('offset', type=int, default=0)
                
                # 限制返回数量，防止内存溢出
                if limit and limit > 10000:
                    return jsonify({'error': 'Limit cannot exceed 10000'}), 400
                
                records = self.db.select(table_name, condition, limit, offset)
                total_count = self.db.count(table_name, condition)
                
                return jsonify({
                    'records': records, 
                    'count': len(records),
                    'total_count': total_count,
                    'has_more': offset + len(records) < total_count
                })
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid condition JSON'}), 400
            except Exception as e:
                return self._handle_api_call(lambda: None)
        
        @self.app.route('/api/tables/<table_name>/records', methods=['PUT'])
        @self._require_api_key
        def update_records(table_name):
            data = request.get_json()
            count = self.db.update(table_name, data.get('condition', {}), data.get('values', {}))
            return jsonify({'message': f'Updated {count} records', 'updated_count': count})
        
        @self.app.route('/api/tables/<table_name>/records', methods=['DELETE'])
        @self._require_api_key
        def delete_records(table_name):
            data = request.get_json()
            count = self.db.delete(table_name, data.get('condition', {}))
            return jsonify({'message': f'Deleted {count} records', 'deleted_count': count})
        
        # 索引和查询路由
        @self.app.route('/api/tables/<table_name>/indexes', methods=['POST'])
        @self._require_api_key
        def create_index(table_name):
            data = request.get_json()
            if not data.get('column'):
                return jsonify({'error': 'Column name is required'}), 400
            return self._handle_api_call(self.db.create_index, table_name, data.get('column'))
        
        @self.app.route('/api/tables/<table_name>/indexes/<column>', methods=['DELETE'])
        @self._require_api_key
        def drop_index(table_name, column):
            return self._handle_api_call(self.db.drop_index, table_name, column)
        
        @self.app.route('/api/tables/<table_name>/count', methods=['GET'])
        @self._require_api_key
        def count_records(table_name):
            condition = json.loads(request.args.get('condition', 'null'))
            return self._handle_api_call(self.db.count, table_name, condition)
        
        @self.app.route('/api/tables/<table_name>/aggregate', methods=['POST'])
        @self._require_api_key
        def aggregate_query(table_name):
            data = request.get_json()
            return self._handle_api_call(self.db.aggregate, table_name, data.get('pipeline', []))
        
        # 表操作路由
        @self.app.route('/api/tables/<table_name>/info', methods=['GET'])
        @self._require_api_key
        def get_table_info(table_name):
            return self._handle_api_call(self.db.get_table_info, table_name)
        
        @self.app.route('/api/tables/<table_name>/alter', methods=['POST'])
        @self._require_api_key
        def alter_table(table_name):
            data = request.get_json()
            return self._handle_api_call(self.db.alter_table, table_name, data.get('action'), **data)
        
        @self.app.route('/api/tables/<old_name>/rename/<new_name>', methods=['POST'])
        @self._require_api_key
        def rename_table(old_name, new_name):
            return self._handle_api_call(self.db.rename_table, old_name, new_name)
        
        @self.app.route('/api/tables/<table_name>/truncate', methods=['POST'])
        @self._require_api_key
        def truncate_table(table_name):
            return self._handle_api_call(self.db.truncate_table, table_name)
        
        @self.app.route('/api/tables/<table_name>/analyze', methods=['GET'])
        @self._require_api_key
        def analyze_table(table_name):
            return self._handle_api_call(self.db.analyze_table, table_name)
        
        @self.app.route('/api/tables/<table_name>/optimize', methods=['POST'])
        @self._require_api_key
        def optimize_table(table_name):
            return self._handle_api_call(self.db.optimize_table, table_name)
        
        # 数据导入导出路由
        @self.app.route('/api/tables/<table_name>/import', methods=['POST'])
        @self._require_api_key
        def import_data(table_name):
            data = request.get_json()
            return self._handle_api_call(self.db.import_data, table_name, 
                                       data.get('data', []), data.get('mode', 'insert'))
        
        @self.app.route('/api/tables/<table_name>/export', methods=['GET'])
        @self._require_api_key
        def export_data(table_name):
            condition = json.loads(request.args.get('condition', 'null'))
            format_type = request.args.get('format', 'json')
            data = self.db.export_data(table_name, condition, format_type)
            
            if format_type == 'json':
                return data, 200, {'Content-Type': 'application/json'}
            return jsonify({'data': data})
        
        # 数据库管理路由
        @self.app.route('/api/database/info', methods=['GET'])
        @self._require_api_key
        def get_database_info():
            return self._handle_api_call(self.db.get_database_info)
        
        @self.app.route('/api/database/vacuum', methods=['POST'])
        @self._require_api_key
        def vacuum_database():
            return self._handle_api_call(self.db.vacuum)
        
        @self.app.route('/api/backup', methods=['POST'])
        @self._require_api_key
        def backup_database():
            data = request.get_json() or {}
            return self._handle_api_call(self.db.backup, data.get('path'))
        
        @self.app.route('/api/restore', methods=['POST'])
        @self._require_api_key
        def restore_database():
            data = request.get_json()
            if not data.get('path'):
                return jsonify({'error': 'Backup path is required'}), 400
            return self._handle_api_call(self.db.restore, data.get('path'))
        
        @self.app.route('/api/query', methods=['POST'])
        @self._require_api_key
        def execute_query():
            data = request.get_json()
            if not data.get('query'):
                return jsonify({'error': 'Query is required'}), 400
            return self._handle_api_call(self.db.execute_sql_like, data.get('query'))
        
        @self.app.route('/api/transaction', methods=['POST'])
        @self._require_api_key
        def execute_transaction():
            data = request.get_json()
            operations = data.get('operations', [])
            
            if not operations:
                return jsonify({'error': 'Operations list is required'}), 400
            
            try:
                results = []
                with self.db.transaction():
                    for op in operations:
                        op_type, table = op.get('type'), op.get('table')
                        
                        if op_type == 'insert':
                            result = self.db.insert(table, op.get('record', {}))
                            results.append({'operation': 'insert', 'success': result})
                        elif op_type == 'update':
                            count = self.db.update(table, op.get('condition', {}), op.get('values', {}))
                            results.append({'operation': 'update', 'updated_count': count})
                        elif op_type == 'delete':
                            count = self.db.delete(table, op.get('condition', {}))
                            results.append({'operation': 'delete', 'deleted_count': count})
                
                return jsonify({'message': 'Transaction completed successfully', 'results': results})
            except Exception as e:
                return jsonify({'error': f'Transaction failed: {str(e)}'}), 500
        
        @self.app.route('/api/config', methods=['GET'])
        @self._require_api_key
        def get_config():
            if not CONFIG_AVAILABLE:
                return jsonify({'error': 'Configuration system not available'}), 500
            
            return jsonify({
                'database': {'path': config.get('database.path'), 'backup_dir': config.get('database.backup_dir')},
                'api': {'host': config.get('api.host'), 'port': config.get('api.port'), 'debug': config.get('api.debug')},
                'logging': {'level': config.get('logging.level')}
            })

    def run(self, host=None, port=None, debug=None):
        """启动API服务器"""
        # 使用配置系统
        if CONFIG_AVAILABLE:
            host = host or config.get('api.host', '127.0.0.1')
            port = port or config.get('api.port', 5000)
            debug = debug if debug is not None else config.get('api.debug', False)
        else:
            host = host or '127.0.0.1'
            port = port or 5000
            debug = debug if debug is not None else False
        
        print(f"ADB API服务器启动在 http://{host}:{port}")
        print(f"数据库: {self.db.db_path}")
        print(f"表数量: {len(self.db.list_tables())}")
        if self.api_key:
            print(f"API密钥验证: 启用")
        if self.rate_limit:
            print(f"速率限制: 启用 (60/分钟)")
        
        self.app.run(host=host, port=port, debug=debug)

# 使用示例
if __name__ == "__main__":
    # 简化初始化
    try:
        db = ADB() if CONFIG_AVAILABLE else ADB("my_database.json", enable_logging=True)
        
        # 创建示例表
        if not db.list_tables():
            user_schema = {
                'name': {'type': str, 'required': True, 'max_length': 50}, 
                'age': {'type': int, 'required': True},
                'email': {'type': str, 'required': False, 'max_length': 100}
            }
            db.create_table("users", user_schema)
            db.insert("users", {"name": "张三", "age": 25, "email": "zhangsan@example.com"})
        
        print(f"数据库路径: {db.db_path}")
        print(f"表列表: {db.list_tables()}")
        
        # 启动API服务器
        if FLASK_AVAILABLE:
            api_key = config.get('api.api_key') if CONFIG_AVAILABLE else "my-secret-key-123"
            api_server = ADBAPIServer(db, api_key=api_key)
            print("准备启动API服务器...")
            # api_server.run()  # 取消注释以启动服务器
        
    except Exception as e:
        print(f"启动失败: {e}")