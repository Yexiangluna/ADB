"""
ADB 配置管理模块
"""

import os
import json
from typing import Dict, Any, Optional
from pathlib import Path

class ADBConfig:
    """ADB配置管理类"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置
        
        Args:
            config_file: 配置文件路径（可选）
        """
        self.config_file = config_file or "config.json"
        self._config = {}
        self._load_default_config()
        self._load_env_config()
        self._load_file_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            # 数据库配置
            'database': {
                'path': './data/adb_database.json',
                'backup_dir': './backups',
                'auto_backup_interval': 3600,  # 秒
                'max_records_per_table': 100000
            },
            
            # 日志配置
            'logging': {
                'level': 'INFO',
                'file': './logs/adb.log',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            },
            
            # API服务器配置
            'api': {
                'host': '127.0.0.1',
                'port': 5000,
                'debug': False,
                'api_key': None,
                'require_api_key': True,
                'max_request_size': 10485760,  # 10MB
                'cors_enabled': False,
                'rate_limiting': {
                    'enabled': False,
                    'requests_per_minute': 60
                }
            },
            
            # 性能配置
            'performance': {
                'index_cache_size': 1000,
                'query_timeout': 30,
                'transaction_timeout': 60,
                'memory_limit': 536870912  # 512MB
            },
            
            # 安全配置
            'security': {
                'allow_schema_changes': True,
                'encrypt_backups': False,
                'audit_logging': False
            },
            
            # 开发配置
            'development': {
                'dev_mode': False,
                'enable_profiling': False,
                'mock_data': False
            }
        }
    
    def _load_env_config(self):
        """从环境变量加载配置"""
        # 数据库配置
        if os.getenv('ADB_DATABASE_PATH'):
            self._config['database']['path'] = os.getenv('ADB_DATABASE_PATH')
        if os.getenv('ADB_BACKUP_DIR'):
            self._config['database']['backup_dir'] = os.getenv('ADB_BACKUP_DIR')
        
        # 日志配置
        if os.getenv('ADB_LOG_LEVEL'):
            self._config['logging']['level'] = os.getenv('ADB_LOG_LEVEL')
        if os.getenv('ADB_LOG_FILE'):
            self._config['logging']['file'] = os.getenv('ADB_LOG_FILE')
        
        # API配置
        if os.getenv('ADB_API_HOST'):
            self._config['api']['host'] = os.getenv('ADB_API_HOST')
        if os.getenv('ADB_API_PORT'):
            self._config['api']['port'] = int(os.getenv('ADB_API_PORT'))
        if os.getenv('ADB_API_DEBUG'):
            self._config['api']['debug'] = os.getenv('ADB_API_DEBUG').lower() == 'true'
        if os.getenv('ADB_API_KEY'):
            self._config['api']['api_key'] = os.getenv('ADB_API_KEY')
        
        # 性能配置
        if os.getenv('ADB_MAX_RECORDS_PER_TABLE'):
            self._config['database']['max_records_per_table'] = int(os.getenv('ADB_MAX_RECORDS_PER_TABLE'))
        if os.getenv('ADB_INDEX_CACHE_SIZE'):
            self._config['performance']['index_cache_size'] = int(os.getenv('ADB_INDEX_CACHE_SIZE'))
        
        # 安全配置
        if os.getenv('ADB_ALLOW_SCHEMA_CHANGES'):
            self._config['security']['allow_schema_changes'] = os.getenv('ADB_ALLOW_SCHEMA_CHANGES').lower() == 'true'
        if os.getenv('ADB_REQUIRE_API_KEY'):
            self._config['api']['require_api_key'] = os.getenv('ADB_REQUIRE_API_KEY').lower() == 'true'
        
        # 开发配置
        if os.getenv('ADB_DEV_MODE'):
            self._config['development']['dev_mode'] = os.getenv('ADB_DEV_MODE').lower() == 'true'
        if os.getenv('ADB_ENABLE_PROFILING'):
            self._config['development']['enable_profiling'] = os.getenv('ADB_ENABLE_PROFILING').lower() == 'true'
    
    def _load_file_config(self):
        """从配置文件加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self._config, file_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告: 无法加载配置文件 {self.config_file}: {e}")
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """递归合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）
        
        Args:
            key: 配置键，如 'database.path' 或 'api.port'
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, file_path: Optional[str] = None):
        """
        保存配置到文件
        
        Args:
            file_path: 保存路径（可选）
        """
        save_path = file_path or self.config_file
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存配置文件失败: {e}")
    
    def create_directories(self):
        """创建必要的目录"""
        dirs_to_create = [
            os.path.dirname(self.get('database.path')),
            self.get('database.backup_dir'),
            os.path.dirname(self.get('logging.file'))
        ]
        
        for dir_path in dirs_to_create:
            if dir_path:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        errors = []
        
        # 验证API端口
        port = self.get('api.port')
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("API端口必须在1-65535之间")
        
        # 验证路径
        db_path = self.get('database.path')
        if not db_path:
            errors.append("数据库路径不能为空")
        
        # 验证日志级别
        log_level = self.get('logging.level')
        if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append("无效的日志级别")
        
        if errors:
            for error in errors:
                print(f"配置错误: {error}")
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """返回完整配置字典"""
        return self._config.copy()

# 全局配置实例
config = ADBConfig()
