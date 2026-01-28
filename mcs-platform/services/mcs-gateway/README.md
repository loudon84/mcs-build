# MCS Gateway Service
外部系统集成网关服务，提供统一的接口访问 ERP 等外部系统。
用于对已经注册外部的接口调用

## 功能

- ERP 订单创建
- ERP 订单查询
- 统一的外部系统接口抽象
- 支持多租户
- 错误处理和重试

## API 端点

### 创建订单

```bash
POST /v1/orders
Content-Type: application/json

{
  "customer_id": "c1",
  "customer_num": "C001",
  "items": [...],
  ...
}
```

**响应**:
```json
{
  "ok": true,
  "sales_order_no": "SO20240123001",
  "order_url": "https://erp.example.com/orders/SO20240123001",
  "order_id": "order-123"
}
```

### 查询订单

```bash
GET /v1/orders/{order_id}
```

## 配置

### 环境变量

```bash
# ERP 系统配置
ERP_BASE_URL=http://erp.example.com
ERP_API_KEY=your_api_key
ERP_TENANT_ID=tenant1

# 数据库
DB_DSN=postgresql://user:password@localhost:5432/mcs_gateway

# 安全
API_KEY=gateway_api_key
JWT_PUBLIC_KEY=your_jwt_public_key
ALLOWED_TENANTS=tenant1,tenant2
```

## 扩展

可以添加更多外部系统客户端：
- CRM 系统
- 财务系统
- 仓储系统
等

