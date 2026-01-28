# MCS Platform API Documentation

## Master Data Service

### GET /v1/masterdata/all
获取所有主数据

### GET /v1/masterdata/version
获取主数据版本号

### POST /v1/masterdata/customers
创建/更新客户

### POST /v1/masterdata/contacts
创建/更新联系人

### PUT /v1/masterdata/bulk
批量更新主数据

## Orchestrator Service

### POST /v1/orchestrations/sales-email/run
运行销售邮件编排

**Request:**
```json
{
  "provider": "imap",
  "account": "sales@example.com",
  "folder": "INBOX",
  "uid": "123",
  "message_id": "msg1",
  "from_email": "customer@example.com",
  "to": ["sales@example.com"],
  "subject": "采购合同",
  "body_text": "请查看附件",
  "received_at": "2024-01-01T00:00:00Z",
  "attachments": []
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "message_id": "msg1",
  "status": "SUCCESS",
  "started_at": "2024-01-01T00:00:00Z",
  "finished_at": "2024-01-01T00:01:00Z",
  "sales_order_no": "SO001",
  "order_url": "https://example.com/orders/SO001"
}
```

### POST /v1/orchestrations/sales-email/replay
重放销售邮件编排

### GET /v1/healthz
健康检查

## Email Listener Service

### POST /v1/webhook/email
接收邮件 Webhook

### POST /v1/trigger/poll
手动触发邮件轮询

### GET /v1/status
服务状态

