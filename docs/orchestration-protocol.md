# 编排协议与 API 端点清单

本文档定义 MCS 编排服务的**控制平面契约**：请求/响应字段、终态与错误码、幂等与重试规则，以及所有编排相关 API 端点的清单。新端点需在此登记，便于兼容性与废弃管理。

---

## 1. 编排协议/契约

### 1.1 请求必填字段（编排入口）

| 接口 | 请求体/来源 | 必填字段说明 |
|------|-------------|--------------|
| `POST /v1/orchestrations/sales-email/run` | `EmailEvent`（见 [libs/contracts](mcs-platform/libs/contracts)） | `message_id`、`from_email`、`subject`、`body_text`、`received_at`、`provider`、`account`、`folder`、`uid`；`attachments` 可为空列表。来源 channel 可由 `provider`/`account` 推断。 |
| `POST /v1/orchestrations/sales-email/replay` | `ReplayRequest` | `message_id` 与 `idempotency_key` 二选一必填。 |
| `POST /v1/orchestrations/sales-email/manual-review/submit` | `ManualReviewSubmitRequest` | `run_id`、`decision`、`operator`、`auth` 必填。 |

编排 run 的入参以 [libs/contracts 的 EmailEvent](mcs-platform/libs/contracts/src/email_event.py) 为准；manual-review 以 [Orchestrator 的 ManualReviewSubmitRequest](mcs-platform/libs/contracts/src/orchestrator.py) 为准。

### 1.2 响应/终态枚举（StatusEnum）

编排结果终态定义在 [libs/contracts/common.py](mcs-platform/libs/contracts/src/common.py) 的 `StatusEnum`：

| 终态 | 含义与使用场景 |
|------|----------------|
| `IGNORED` | 邮件被忽略（非合同/不符合条件） |
| `UNKNOWN_CONTACT` | 发件人未匹配到联系人 |
| `MANUAL_REVIEW` | 进入人工审核（多候选或低置信度） |
| `CONTRACT_PARSE_FAILED` | 合同解析失败（Dify/PDF） |
| `ORDER_PAYLOAD_BLOCKED` | 订单载荷被 Dify 或策略拦截 |
| `ERP_ORDER_FAILED` | 创建 ERP 订单失败 |
| `SUCCESS` | 编排成功完成，订单已创建 |
| `PENDING` | 运行中/未完成（中间状态） |
| `FAILED` | 通用失败 |
| `RUNNING` | 运行中（中间状态） |

响应模型 [OrchestratorRunResult](mcs-platform/libs/contracts/src/orchestrator.py) 包含：`run_id`、`message_id`、`status`（终态）、`started_at`、`finished_at`、`idempotency_key`、`customer_id`、`contact_id`、`file_url`、`sales_order_no`、`order_url`、`warnings` 等。

### 1.3 错误码列表（error_code）

业务/流程错误使用 `error_code` 字符串，与 [orchestrator/src/errors.py](mcs-platform/orchestrator/src/errors.py) 及 [.cursor/rules/namespace.mdc](.cursor/rules/namespace.mdc) 一致：

| 错误码 | 含义 |
|--------|------|
| `MASTERDATA_INVALID` | 主数据无效或加载失败 |
| `CONTACT_NOT_FOUND` | 未找到匹配联系人 |
| `NOT_CONTRACT_MAIL` | 非合同邮件 |
| `PDF_NOT_FOUND` | 未找到 PDF 附件 |
| `CUSTOMER_MATCH_LOW_SCORE` | 客户匹配分数过低 |
| `CUSTOMER_CONTACT_MISMATCH` | 客户与联系人不一致 |
| `FILE_UPLOAD_FAILED` | 文件上传失败 |
| `DIFY_CONTRACT_FAILED` | Dify 合同解析失败 |
| `DIFY_ORDER_PAYLOAD_BLOCKED` | Dify 订单载荷被拦截 |
| `ERP_CREATE_FAILED` | ERP 订单创建失败 |
| `ERP_CONNECTION_FAILED` | ERP 连接失败 |
| `ERP_AUTH_FAILED` | ERP 认证失败 |
| `ERP_INVALID_RESPONSE` | ERP 响应无效 |
| `MULTI_PDF_ATTACHMENTS` | 多 PDF 附件无法唯一选择 |
| `MULTI_CUSTOMER_AMBIGUOUS` | 多客户候选歧义 |
| `FILE_ACCESS_BLOCKED` | 文件访问被拒绝 |
| `RUN_NOT_IN_MANUAL_REVIEW` | 该 run 未处于人工审核状态 |
| `INVALID_DECISION` | 人工审核决策无效 |
| `STALE_DECISION` | 决策已过期（状态已变更） |
| `PERMISSION_DENIED` | 权限拒绝 |

API 层将 `OrchestratorError` 映射为 HTTP 4xx/5xx 与 `detail`；对外可返回 `ErrorInfo` 结构（`code`、`reason`、`details`）。

### 1.4 幂等与重试规则

- **run**：请求体为 `EmailEvent`，必含 `message_id`。幂等键由服务端在编排图内根据 `message_id` 等生成并写入 `idempotency_records`；同一次「逻辑请求」重复调用会因相同幂等键命中已有记录而返回已有结果或短路。
- **replay**：请求体须提供 `message_id` 或 `idempotency_key` 之一；用于按消息或按幂等键重放，服务端会校验并返回已有结果或执行重放。
- **manual-review/submit**：必须带 `run_id` 与 `decision`；同一 `run_id` 的重复提交由业务逻辑判断（如 STALE_DECISION），客户端应避免重复提交。

**重试建议**：5xx 可重试（指数退避）；4xx 一般不重试（除 429/限流策略）；幂等接口（run/replay/submit）重试时保持同一 `message_id`/`idempotency_key`/`run_id`。

---

## 2. API 端点清单

以下为编排服务（orchestrator）及统一网关可代理的端点。列：**方法、路径、用途、稳定性、幂等键要求**。

### 2.1 编排

| 方法 | 路径 | 用途 | 稳定性 | 幂等键要求 |
|------|------|------|--------|------------|
| POST | `/v1/orchestrations/sales-email/run` | 执行销售邮件编排 | 稳定 | 服务端按 message_id 等生成 |
| POST | `/v1/orchestrations/sales-email/replay` | 按 message_id 或 idempotency_key 重放 | 稳定 | 请求体提供 message_id 或 idempotency_key |
| POST | `/v1/orchestrations/sales-email/manual-review/submit` | 提交人工审核决策并继续执行 | 稳定 | run_id + decision，业务去重 |

### 2.2 健康

| 方法 | 路径 | 用途 | 稳定性 | 幂等键要求 |
|------|------|------|--------|------------|
| GET | `/healthz` | 健康检查 | 稳定 | 无 |

### 2.3 主数据（/v1/masterdata）

| 方法 | 路径 | 用途 | 稳定性 | 幂等键要求 |
|------|------|------|--------|------------|
| GET | `/v1/masterdata/customers` | 获取客户列表 | 稳定 | 无 |
| GET | `/v1/masterdata/contacts` | 获取联系人列表 | 稳定 | 无 |
| GET | `/v1/masterdata/companies` | 获取公司列表 | 稳定 | 无 |
| GET | `/v1/masterdata/products` | 获取产品列表 | 稳定 | 无 |
| GET | `/v1/masterdata/all` | 获取全部主数据（带缓存） | 稳定 | 无 |
| GET | `/v1/masterdata/version` | 获取主数据版本号 | 稳定 | 无 |
| POST | `/v1/masterdata/customers` | 创建/更新客户 | 稳定 | 无 |
| POST | `/v1/masterdata/contacts` | 创建/更新联系人 | 稳定 | 无 |
| PUT | `/v1/masterdata/bulk` | 批量更新主数据 | 稳定 | 无 |

### 2.4 网关/订单（/v1/orders）

| 方法 | 路径 | 用途 | 稳定性 | 幂等键要求 |
|------|------|------|--------|------------|
| POST | `/v1/orders` | 在 ERP 创建订单 | 稳定 | 由调用方/网关约定 |
| GET | `/v1/orders/{order_id}` | 查询订单 | 稳定 | 无 |

### 2.5 监听（/v1/listener）

| 方法 | 路径 | 用途 | 稳定性 | 幂等键要求 |
|------|------|------|--------|------------|
| POST | `/v1/listener/webhook/email` | 接收邮件 Webhook | 稳定 | 无 |
| POST | `/v1/listener/webhook/wechat` | 接收企业微信 Webhook | 稳定 | 无 |
| POST | `/v1/listener/trigger/poll` | 手动触发轮询 | 稳定 | 无 |
| GET | `/v1/listener/status` | 监听器状态 | 稳定 | 无 |

---

**说明**：新增或变更编排相关端点时，应同步更新本文档的端点清单与协议条款，并评估版本兼容（如需要则使用新路径或版本前缀）。
