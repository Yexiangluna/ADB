"""
ADB API 服务器示例
"""

from adb import ADB, ADBAPIServer

def setup_sample_data(db):
    """设置示例数据"""
    # 创建产品表
    product_schema = {
        'name': {'type': str, 'required': True, 'max_length': 100},
        'price': {'type': float, 'required': True},
        'category': {'type': str, 'required': True, 'max_length': 50},
        'stock': {'type': int, 'required': True}
    }
    
    if db.create_table("products", product_schema):
        print("创建产品表成功")
        
        # 插入示例产品
        products = [
            {"name": "iPhone 15", "price": 999.99, "category": "手机", "stock": 50},
            {"name": "MacBook Pro", "price": 1999.99, "category": "电脑", "stock": 30},
            {"name": "iPad Air", "price": 599.99, "category": "平板", "stock": 40},
            {"name": "AirPods Pro", "price": 249.99, "category": "音频", "stock": 100}
        ]
        
        for product in products:
            db.insert("products", product)
        
        # 创建索引
        db.create_index("products", "category")
        db.create_index("products", "price")
        
        print(f"插入了 {len(products)} 个产品")
    
    # 创建订单表
    order_schema = {
        'product_id': {'type': int, 'required': True},
        'quantity': {'type': int, 'required': True},
        'customer_name': {'type': str, 'required': True, 'max_length': 100},
        'total_amount': {'type': float, 'required': True}
    }
    
    if db.create_table("orders", order_schema):
        print("创建订单表成功")

def main():
    """启动API服务器示例"""
    print("=== ADB API 服务器示例 ===\n")
    
    # 创建数据库
    db = ADB("api_example.json", enable_logging=True)
    
    # 设置示例数据
    setup_sample_data(db)
    
    # 创建API服务器
    api_key = "demo-api-key-12345"
    api_server = ADBAPIServer(db, api_key=api_key)
    
    print(f"数据库表: {db.list_tables()}")
    print(f"产品数量: {db.count('products')}")
    print("\n=== API 服务器信息 ===")
    print(f"服务地址: http://127.0.0.1:5000")
    print(f"API 密钥: {api_key}")
    print("\n=== 可用的 API 端点 ===")
    print("GET  /api/health                     - 健康检查")
    print("GET  /api/tables                     - 列出所有表")
    print("POST /api/tables                     - 创建表")
    print("GET  /api/tables/products/records    - 查询产品")
    print("POST /api/tables/products/records    - 添加产品")
    print("PUT  /api/tables/products/records    - 更新产品")
    print("DELETE /api/tables/products/records  - 删除产品")
    print("\n=== 示例 API 调用 ===")
    print("curl -H 'X-API-Key: demo-api-key-12345' http://localhost:5000/api/health")
    print("curl -H 'X-API-Key: demo-api-key-12345' http://localhost:5000/api/tables")
    print("curl -H 'X-API-Key: demo-api-key-12345' http://localhost:5000/api/tables/products/records")
    print("\n启动服务器中...")
    
    # 启动服务器
    api_server.run(debug=True)

if __name__ == "__main__":
    main()
