# MCS Platform Runbook

## 本地启动

### 1. 环境准备

```bash
# 创建 conda 环境
conda create -n mcs-platform python=3.12
conda activate mcs-platform

# 安装依赖
cd mcs-platform/libs/contracts
pip install -e .

cd ../../services/mcs-masterdata
pip install -e .

cd ../mcs-email-listener
pip install -e .

cd ../mcs-orchestrator
pip install -e .
```

### 2. 数据库设置

```bash
# 启动 PostgreSQL
docker run -d --name postgres -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15

# 运行迁移
cd services/mcs-masterdata
alembic upgrade head

cd ../mcs-orchestrator
alembic upgrade head
```

### 3. 配置环境变量

创建 `.env` 文件：

```env
# Master Data Service
DB_DSN=postgresql://user:password@localhost:5432/mcs_masterdata
REDIS_URL=redis://localhost:6379/0

# Orchestrator Service
DB_DSN=postgresql://user:password@localhost:5432/mcs_orchestrator
DIFY_BASE_URL=https://api.dify.ai
DIFY_CONTRACT_APP_KEY=your_key
DIFY_ORDER_APP_KEY=your_key
MASTERDATA_API_URL=http://localhost:8002

# Email Listener
IMAP_HOST=imap.example.com
IMAP_USER=sales@example.com
IMAP_PASS=password
ORCHESTRATOR_API_URL=http://localhost:8000
```

### 4. 启动服务

```bash
# Terminal 1: Master Data Service
cd services/mcs-masterdata
python -m mcs_masterdata.api.main

# Terminal 2: Orchestrator Service
cd services/mcs-orchestrator
python -m mcs_orchestrator.api.main

# Terminal 3: Email Listener Service
cd services/mcs-email-listener
python -m mcs_email_listener.api.main
```

## 常见错误码

- `MASTERDATA_INVALID`: 主数据无效
- `CONTACT_NOT_FOUND`: 联系人未找到
- `NOT_CONTRACT_MAIL`: 非合同邮件
- `PDF_NOT_FOUND`: PDF 附件未找到
- `CUSTOMER_MATCH_LOW_SCORE`: 客户匹配分数过低
- `CUSTOMER_CONTACT_MISMATCH`: 客户与联系人不匹配
- `FILE_UPLOAD_FAILED`: 文件上传失败
- `DIFY_CONTRACT_FAILED`: Dify 合同识别失败
- `DIFY_ORDER_PAYLOAD_BLOCKED`: Dify 订单生成被阻止
- `ERP_CREATE_FAILED`: ERP 订单创建失败

## Replay 功能

```bash
# 通过 message_id replay
curl -X POST http://localhost:8000/v1/orchestrations/sales-email/replay \
  -H "Content-Type: application/json" \
  -d '{"message_id": "msg123"}'
```

## 排查 Dify 输出非 JSON

1. 检查 Dify chatflow 配置
2. 查看 `raw_answer` 字段
3. 检查 Dify 日志

## 查看 Idempotency 命中

```sql
SELECT * FROM idempotency_records WHERE idempotency_key = 'xxx';
```

