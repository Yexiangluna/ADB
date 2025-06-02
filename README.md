# ADB (API Database) 使用说明文档

## 📖 简介

ADB是一个轻量级的基于API的数据库管理系统，专为小型应用、原型开发和测试环境设计。它以JSON文件作为存储介质，提供完整的CRUD操作和高级数据库功能。

### 🎯 核心特性

- ✅ **基于API设计**：所有操作通过函数调用实现
- 🔧 **嵌入式运行**：直接集成到Python应用中
- 📊 **JSON存储**：轻量级文件存储，易于管理
- 🔍 **索引支持**：提高查询性能
- 🛡️ **事务处理**：确保数据一致性
- 🌐 **Web API**：可选的HTTP服务接口
- 🔒 **数据验证**：表结构约束和类型检查
- ⚙️ **配置管理**：支持环境变量和配置文件
- 🔧 **表结构管理**：动态修改表结构
- 🛡️ **安全增强**：API密钥验证、速率限制、请求大小限制
- ⚡ **性能优化**：原子写入、批量操作、智能缓存
- 🧪 **完整测试**：单元测试和集成测试
- 📚 **丰富示例**：快速上手和学习

## 🚀 快速开始

### 项目初始化

```bash
# 1. 克隆或下载项目
git clone https://github.com/Yexiangluna/ADB.git
cd ADB

# 2. 运行设置脚本
python scripts/setup.py

# 3. 配置环境变量（可选）
cp .env.template .env
# 编辑 .env 文件

# 4. 运行测试验证安装
python scripts/run_tests.py

# 5. 运行基本示例
python examples/basic_usage.py

# 6. 启动API服务器（可选）
python examples/api_server_example.py
```

### 目录结构

```
ADB/
├── adb.py                    # 核心数据库模块
├── config.py                 # 配置管理模块
├── requirements.txt          # 项目依赖
├── Readme.md                # 使用文档
├── .gitignore               # Git忽略文件
├── .env.template            # 环境变量模板
├── config.json              # 配置文件
├── data/                    # 数据目录
├── backups/                 # 备份目录
├── logs/                    # 日志目录
├── tests/                   # 测试目录
│   ├── __init__.py
│   ├── test_adb.py         # 核心功能测试
│   └── test_api.py         # API功能测试
├── examples/                # 示例目录
│   ├── __init__.py
│   ├── basic_usage.py      # 基本使用示例
│   └── api_server_example.py # API服务器示例
└── scripts/                 # 工具脚本
    ├── setup.py            # 项目设置脚本
    └── run_tests.py        # 测试运行脚本
```

## 🧪 运行测试

```bash
# 运行所有测试
python scripts/run_tests.py

# 运行特定测试
python -m unittest tests.test_adb.TestADB.test_create_table
python -m unittest tests.test_api.TestADBAPI.test_health_check

# 运行测试并查看覆盖率（需要安装coverage）
pip install coverage
coverage run -m unittest discover tests
coverage report
coverage html  # 生成HTML报告
```

## 📚 示例和教程

### 基本使用示例

```bash
python examples/basic_usage.py
```

这个示例展示了：
- 创建表和定义结构
- 插入和查询数据
- 创建索引
- 使用事务
- 聚合查询
- 数据备份

### API服务器示例

```bash
python examples/api_server_example.py
```

这个示例展示了：
- 启动Web API服务器
- 创建示例数据
- API端点使用方法
- 安全配置

## 🔧 开发和测试

### 添加新功能

1. 在 `adb.py` 中实现新功能
2. 在 `tests/test_adb.py` 中添加测试
3. 如果有API相关功能，在 `tests/test_api.py` 中添加测试
4. 在 `examples/` 中添加使用示例
5. 更新文档

### 测试驱动开发

```python
# 1. 先写测试
def test_new_feature(self):
    result = self.db.new_feature("param")
    self.assertTrue(result)

# 2. 运行测试（应该失败）
python -m unittest tests.test_adb.TestADB.test_new_feature

# 3. 实现功能
def new_feature(self, param):
    # 实现逻辑
    return True

# 4. 再次运行测试（应该通过）
```

## 📊 性能测试

创建性能测试脚本：

```python
# performance_test.py
import time
from adb import ADB

def test_bulk_insert():
    db = ADB(":memory:")  # 内存数据库
    db.create_table("test")
    
    start_time = time.time()
    with db.transaction():
        for i in range(10000):
            db.insert("test", {"id": i, "data": f"record_{i}"})
    
    elapsed = time.time() - start_time
    print(f"插入10000条记录耗时: {elapsed:.2f}秒")
```

## 🚀 部署建议

### 生产环境配置

```json
{
  "database": {
    "path": "/opt/adb/data/production.json",
    "backup_dir": "/opt/adb/backups",
    "max_records_per_table": 50000
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "require_api_key": true,
    "rate_limiting": {"enabled": true}
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/adb/production.log"
  }
}
```

### Docker部署（可选）

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python scripts/setup.py

EXPOSE 5000
CMD ["python", "examples/api_server_example.py"]
```

## 📦 打包和分发

### 创建可执行文件

ADB 支持多种打包方式，可以创建无需Python环境的可执行文件：

```bash
# Windows 一键打包
build.bat

# Linux/Mac 一键打包
chmod +x build.sh
./build.sh

# 手动打包
python build_exe.py
```

### 打包选项

1. **PyInstaller** (推荐)
   - 生成单个可执行文件
   - 包含所有依赖
   - 启动速度快

2. **cx_Freeze**
   - 跨平台兼容性好
   - 文件结构清晰
   - 体积相对较小

3. **便携版**
   - 需要Python环境
   - 体积最小
   - 易于修改和调试

### 安装包类型

- **Windows**: 
  - 可执行文件 (.exe)
  - NSIS 安装程序
  - 便携版 (.zip)

- **Linux**:
  - 可执行文件
  - Shell 安装脚本
  - 便携版 (.tar.gz)

- **macOS**:
  - 应用程序包 (.app)
  - DMG 安装镜像
  - 便携版 (.tar.gz)

### 分发结构

```
dist/
├── pyinstaller/          # PyInstaller 输出
│   └── ADB/
│       ├── adb.exe
│       ├── adb-server.exe
│       ├── config.json
│       └── ...
├── portable/             # 便携版
│   ├── adb.py
│   ├── adb.bat / adb
│   ├── config.json
│   └── ...
└── ADB-Installer.exe     # Windows 安装程序
```

### 使用打包后的程序

```bash
# 命令行工具
adb --help
adb create-table users
adb list-tables
adb insert users '{"name":"张三","age":25}'
adb select users --limit 10

# API 服务器
adb-server --host 0.0.0.0 --port 8080
```

### 部署配置

生产环境部署建议：

```json
{
  "database": {
    "path": "/var/lib/adb/data/production.json",
    "backup_dir": "/var/lib/adb/backups",
    "max_records_per_table": 50000
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8080,
    "debug": false,
    "require_api_key": true
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/adb/production.log"
  }
}
```

## 🔍 故障排除

### 常见问题

1. **测试失败**
   ```bash
   # 检查依赖是否安装
   pip install -r requirements.txt
   
   # 检查Python版本（需要3.7+）
   python --version
   ```

2. **API服务器启动失败**
   ```bash
   # 检查端口是否被占用
   netstat -an | grep 5000
   
   # 检查Flask是否安装
   pip install flask
   ```

3. **数据库文件问题**
   ```bash
   # 检查文件权限
   ls -la data/
   
   # 重新创建数据目录
   python scripts/setup.py
   ```

## 📈 项目发展计划

### 已完成功能 ✅
- 核心CRUD操作
- 事务支持
- 索引系统
- Web API接口
- 数据验证
- 配置管理
- 完整测试套件
- 使用示例

### 计划中功能 🚧
- 数据加密
- 分布式支持
- 查询优化器
- 数据迁移工具
- 图形界面管理工具
- 更多数据类型支持

### 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/new-feature`)
3. 添加测试并确保通过
4. 提交更改 (`git commit -am 'Add new feature'`)
5. 推送到分支 (`git push origin feature/new-feature`)
6. 创建 Pull Request

---

**最后更新**: 2025年6月 | **版本**: 1.3.0 | **许可证**: MIT


