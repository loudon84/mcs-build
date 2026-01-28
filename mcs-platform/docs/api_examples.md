# MCS Platform API 调用范例

## 基础配置

### 环境变量示例

```bash
# .env 文件示例
# Master Data Service
DB_DSN=postgresql://mcs:password@localhost:5432/mcs_masterdata
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=INFO

# Orchestrator Service
DB_DSN=postgresql://mcs:password@localhost:5432/mcs_orchestrator
DIFY_BASE_URL=https://api.dify.ai
DIFY_CONTRACT_APP_KEY=app-xxxxx
DIFY_ORDER_APP_KEY=app-yyyyy
FILE_SERVER_BASE_URL=http://localhost:8001
FILE_SERVER_API_KEY=file_server_key
GATEWAY_URL=http://localhost:8003
MASTERDATA_API_URL=http://localhost:8002
MASTERDATA_API_KEY=masterdata_key
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=sales@example.com
SMTP_PASS=smtp_password

# Email Listener Service
IMAP_HOST=imap.example.com
IMAP_PORT=993
IMAP_USER=sales@example.com
IMAP_PASS=imap_password
ORCHESTRATOR_API_URL=http://localhost:8000
ORCHESTRATOR_API_KEY=orchestrator_key
```

## 1. Master Data Service API

### 1.1 获取所有主数据

```bash
curl -X GET "http://localhost:8002/v1/masterdata/all" \
  -H "X-API-Key: masterdata_key" \
  -H "Content-Type: application/json"
```

**响应示例**:
```json
{
  "customers": [
    {
      "customer_id": "c1",
      "customer_num": "C001",
      "name": "客户A",
      "company_id": "comp1"
    }
  ],
  "contacts": [
    {
      "contact_id": "ct1",
      "email": "contact@example.com",
      "name": "联系人A",
      "customer_id": "c1",
      "telephone": "13800138000"
    }
  ],
  "companys": [],
  "products": []
}
```

### 1.2 创建/更新客户

```bash
curl -X POST "http://localhost:8002/v1/masterdata/customers" \
  -H "X-API-Key: masterdata_key" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "c1",
    "customer_num": "C001",
    "name": "客户A",
    "company_id": "comp1"
  }'
```

### 1.3 批量更新主数据

```bash
curl -X PUT "http://localhost:8002/v1/masterdata/bulk" \
  -H "X-API-Key: masterdata_key" \
  -H "Content-Type: application/json" \
  -d '{
    "customers": [...],
    "contacts": [...],
    "companys": [...],
    "products": [...]
  }'
```

### 1.4 获取主数据版本

```bash
curl -X GET "http://localhost:8002/v1/masterdata/version" \
  -H "X-API-Key: masterdata_key"
```

**响应**:
```json
{
  "version": 42
}
```

## 2. Orchestrator Service API

### 2.1 运行销售邮件编排（正常流程）

```bash
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/run" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-12345" \
  -d '{
    "provider": "imap",
    "account": "sales@example.com",
    "folder": "INBOX",
    "uid": "12345",
    "message_id": "<msg123@example.com>",
    "from_email": "customer@example.com",
    "to": ["sales@example.com"],
    "subject": "采购合同",
    "body_text": "请查看附件中的采购合同",
    "received_at": "2024-01-23T10:00:00Z",
    "attachments": [
      {
        "attachment_id": "att1",
        "filename": "C001_采购合同.pdf",
        "content_type": "application/pdf",
        "size": 102400,
        "sha256": "abc123...",
        "bytes_b64": "JVBERi0xLjQK..."
      }
    ]
  }'
```

**成功响应**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "<msg123@example.com>",
  "status": "SUCCESS",
  "started_at": "2024-01-23T10:00:00Z",
  "finished_at": "2024-01-23T10:01:30Z",
  "idempotency_key": "abc123...",
  "customer_id": "c1",
  "contact_id": "ct1",
  "file_url": "http://localhost:8001/files/abc123",
  "sales_order_no": "SO20240123001",
  "order_url": "https://erp.example.com/orders/SO20240123001",
  "warnings": [],
  "errors": []
}
```

### 2.2 运行销售邮件编排（触发 MANUAL_REVIEW - 多 PDF）

```bash
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/run" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "imap",
    "account": "sales@example.com",
    "folder": "INBOX",
    "uid": "12346",
    "message_id": "<msg124@example.com>",
    "from_email": "customer@example.com",
    "to": ["sales@example.com"],
    "subject": "采购合同",
    "body_text": "请查看附件",
    "received_at": "2024-01-23T10:05:00Z",
    "attachments": [
      {
        "attachment_id": "att1",
        "filename": "合同1.pdf",
        "content_type": "application/pdf",
        "size": 102400,
        "sha256": "abc123...",
        "bytes_b64": "JVBERi0xLjQK..."
      },
      {
        "attachment_id": "att2",
        "filename": "合同2.pdf",
        "content_type": "application/pdf",
        "size": 204800,
        "sha256": "def456...",
        "bytes_b64": "JVBERi0xLjQK..."
      }
    ]
  }'
```

**响应（MANUAL_REVIEW）**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440001",
  "message_id": "<msg124@example.com>",
  "status": "MANUAL_REVIEW",
  "started_at": "2024-01-23T10:05:00Z",
  "finished_at": "2024-01-23T10:05:05Z",
  "manual_review": {
    "reason_code": "MULTI_PDF_ATTACHMENTS",
    "created_at": "2024-01-23T10:05:05Z",
    "candidates": {
      "pdfs": [
        {
          "attachment_id": "att1",
          "filename": "合同1.pdf",
          "sha256": "abc123...",
          "size": 102400,
          "suggested": false
        },
        {
          "attachment_id": "att2",
          "filename": "合同2.pdf",
          "sha256": "def456...",
          "size": 204800,
          "suggested": true
        }
      ],
      "customers": [],
      "contacts": []
    }
  },
  "warnings": [],
  "errors": [
    {
      "code": "MULTI_PDF_ATTACHMENTS",
      "reason": "Multiple PDF attachments found (2), manual selection required"
    }
  ]
}
```

### 2.3 提交 Manual Review 决策（RESUME）

```bash
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/manual-review/submit" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: req-12346" \
  -d '{
    "run_id": "550e8400-e29b-41d4-a716-446655440001",
    "message_id": "<msg124@example.com>",
    "decision": {
      "action": "RESUME",
      "selected_customer_id": "c1",
      "selected_contact_id": "ct1",
      "selected_attachment_id": "att2",
      "override": {
        "customer_num": "C001",
        "po_number": "PO20240123"
      },
      "comment": ""
    },
    "operator": {
      "user_id": "user123",
      "user_name": "张三",
      "department": "销售部"
    },
    "auth": {
      "tenant_id": "tenant1",
      "scopes": ["mcs:sales_email:manual_review"],
      "request_id": "req-12346"
    }
  }'
```

**成功响应**:
```json
{
  "ok": true,
  "status": "RESUMING",
  "resume": {
    "from_node": "match_customer",
    "planned_path": [
      "match_customer",
      "upload_pdf",
      "call_dify_contract",
      "call_dify_order_payload",
      "call_gateway",
      "notify_sales",
      "finalize"
    ]
  },
  "audit_id": "audit-event-uuid",
  "run_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 2.4 提交 Manual Review 决策（BLOCK）

```bash
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/manual-review/submit" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "550e8400-e29b-41d4-a716-446655440001",
    "message_id": "<msg124@example.com>",
    "decision": {
      "action": "BLOCK",
      "comment": "合同内容不符合要求，需要重新协商"
    },
    "operator": {
      "user_id": "user123",
      "user_name": "张三",
      "department": "销售部"
    },
    "auth": {
      "tenant_id": "tenant1",
      "scopes": ["mcs:sales_email:manual_review"],
      "request_id": "req-12347"
    }
  }'
```

**响应**:
```json
{
  "ok": true,
  "status": "BLOCKED",
  "final_status": "MANUAL_REVIEW",
  "audit_id": "audit-event-uuid",
  "run_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 2.5 重放编排（Replay）

```bash
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/replay" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "<msg123@example.com>"
  }'
```

**响应**:
```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "message_id": "<msg123@example.com>",
  "status": "SUCCESS",
  "started_at": "2024-01-23T10:00:00Z",
  "finished_at": "2024-01-23T10:01:30Z",
  "sales_order_no": "SO20240123001",
  "order_url": "https://erp.example.com/orders/SO20240123001"
}
```

### 2.6 健康检查

```bash
curl -X GET "http://localhost:8000/v1/orchestrations/healthz"
```

**响应**:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "dify": "ok"
  }
}
```

## 3. Email Listener Service API

### 3.1 接收邮件 Webhook

```bash
curl -X POST "http://localhost:8001/v1/webhook/email" \
  -H "Content-Type: application/json" \
  -d '{
    "account": "sales@example.com",
    "message_id": "<msg125@example.com>",
    "from": "customer@example.com",
    "subject": "采购合同",
    "body": "请查看附件",
    "attachments": [...]
  }'
```

### 3.2 手动触发邮件轮询

```bash
curl -X POST "http://localhost:8001/v1/trigger/poll" \
  -H "X-API-Key: email_listener_key"
```

### 3.3 服务状态

```bash
curl -X GET "http://localhost:8001/v1/status"
```

## 4. Python SDK 调用示例

### 4.1 使用 httpx 调用 Orchestrator API

```python
import httpx
import asyncio

async def run_orchestration():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/orchestrations/sales-email/run",
            headers={
                "X-API-Key": "orchestrator_key",
                "X-Request-ID": "req-12345",
                "Content-Type": "application/json",
            },
            json={
                "provider": "imap",
                "account": "sales@example.com",
                "folder": "INBOX",
                "uid": "12345",
                "message_id": "<msg123@example.com>",
                "from_email": "customer@example.com",
                "to": ["sales@example.com"],
                "subject": "采购合同",
                "body_text": "请查看附件",
                "received_at": "2024-01-23T10:00:00Z",
                "attachments": [
                    {
                        "attachment_id": "att1",
                        "filename": "contract.pdf",
                        "content_type": "application/pdf",
                        "size": 102400,
                        "sha256": "abc123...",
                        "bytes_b64": "JVBERi0xLjQK...",
                    }
                ],
            },
            timeout=180.0,  # 3 minutes for full orchestration
        )
        response.raise_for_status()
        return response.json()

# 运行
result = asyncio.run(run_orchestration())
print(result)
```

### 4.2 提交 Manual Review 决策

```python
async def submit_manual_review(run_id: str, customer_id: str, attachment_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/orchestrations/sales-email/manual-review/submit",
            headers={
                "X-API-Key": "orchestrator_key",
                "X-Request-ID": "req-12346",
                "Content-Type": "application/json",
            },
            json={
                "run_id": run_id,
                "decision": {
                    "action": "RESUME",
                    "selected_customer_id": customer_id,
                    "selected_attachment_id": attachment_id,
                },
                "operator": {
                    "user_id": "user123",
                    "user_name": "张三",
                    "department": "销售部",
                },
                "auth": {
                    "tenant_id": "tenant1",
                    "scopes": ["mcs:sales_email:manual_review"],
                    "request_id": "req-12346",
                },
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
```

## 5. 错误处理示例

### 5.1 权限错误

```json
{
  "ok": false,
  "error_code": "PERMISSION_DENIED",
  "reason": "Missing required scope: mcs:sales_email:manual_review",
  "run_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 5.2 Run 状态错误

```json
{
  "ok": false,
  "error_code": "RUN_NOT_IN_MANUAL_REVIEW",
  "reason": "Run 550e8400... is in status SUCCESS, expected MANUAL_REVIEW",
  "run_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 5.3 无效决策

```json
{
  "ok": false,
  "error_code": "INVALID_DECISION",
  "reason": "selected_customer_id is required for RESUME action",
  "run_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

## 6. 完整流程示例

### 场景：正常流程（自动处理）

```bash
# Step 1: 邮件监听服务检测到新邮件，触发编排
# (自动执行，无需手动调用)

# Step 2: 查询编排结果（可选）
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/replay" \
  -H "X-API-Key: orchestrator_key" \
  -d '{"message_id": "<msg123@example.com>"}'
```

### 场景：需要人工审核（Manual Review）

```bash
# Step 1: 编排进入 MANUAL_REVIEW 状态
# (自动执行，返回 run_id 和 candidates)

# Step 2: 人工审核，提交决策
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/manual-review/submit" \
  -H "X-API-Key: orchestrator_key" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "550e8400-e29b-41d4-a716-446655440001",
    "decision": {
      "action": "RESUME",
      "selected_customer_id": "c1",
      "selected_attachment_id": "att2"
    },
    "operator": {
      "user_id": "user123",
      "user_name": "张三"
    },
    "auth": {
      "tenant_id": "tenant1",
      "scopes": ["mcs:sales_email:manual_review"],
      "request_id": "req-12346"
    }
  }'

# Step 3: 查询最终结果
curl -X POST "http://localhost:8000/v1/orchestrations/sales-email/replay" \
  -H "X-API-Key: orchestrator_key" \
  -d '{"message_id": "<msg124@example.com>"}'
```

## 7. 监控和调试

### 7.1 查看 Prometheus 指标

```bash
curl http://localhost:8000/metrics
```

### 7.2 查询审计日志

```sql
-- 查询特定 run 的审计事件
SELECT * FROM audit_events 
WHERE run_id = '550e8400-e29b-41d4-a716-446655440001'
ORDER BY created_at;

-- 查询 Manual Review 决策
SELECT * FROM audit_events 
WHERE step = 'manual_review_submit'
ORDER BY created_at DESC
LIMIT 10;
```

### 7.3 查询 Idempotency 记录

```sql
SELECT * FROM idempotency_records 
WHERE idempotency_key = 'abc123...';
```

## 8. 常见问题

### Q1: 如何获取 run_id？
A: `run_id` 在调用 `/sales-email/run` 时返回，或通过 `message_id` 查询 `orchestration_runs` 表。

### Q2: 如何查看候选列表？
A: 当 status 为 `MANUAL_REVIEW` 时，响应中的 `manual_review.candidates` 字段包含所有候选。

### Q3: Resume 失败怎么办？
A: 检查错误响应中的 `error_code` 和 `reason`，常见原因：
- Run 不在 MANUAL_REVIEW 状态
- 权限不足
- 决策字段无效

### Q4: 如何验证幂等性？
A: 使用相同的 `message_id`、`file_sha256` 和 `customer_id` 再次调用，应该返回已存在的订单。

