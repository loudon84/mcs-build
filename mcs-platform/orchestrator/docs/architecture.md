# MCS-Orchestrator 软件系统架构分析

本文档对 `mcs-orchestrator` 代码目录作为软件系统进行结构化分析，涵盖整体架构、入口与生命周期、核心模块、扩展点、隐含假设及接口示例。

---

## 1. 整体架构与核心抽象

### 1.1 系统定位

- **角色**：MCS 平台中的编排服务（Orchestration Service），基于 **LangGraph** 实现有状态工作流，对外提供 **FastAPI** HTTP API。
- **核心能力**：接收外部事件（如邮件事件），驱动「销售邮件」等业务图执行，完成联系人匹配、合同识别、订单生成、人工审核等步骤，并持久化运行记录与审计。

### 1.2 分层与依赖关系

```
┌─────────────────────────────────────────────────────────────────┐
│  HTTP API (FastAPI)                                              │
│  api/main.py, api/routes.py, api/deps.py, api/middleware.py     │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Orchestration Layer                                             │
│  graphs/sales_email/graph.py, state.py, resume.py                 │
│  graphs/registry.py                                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Nodes (LangGraph 节点)                                           │
│  graphs/sales_email/nodes/*.py                                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────┐
│  Infrastructure: db/repo.py, db/checkpoint, tools/*,             │
│  observability/*, errors.py, settings.py                          │
└─────────────────────────────────────────────────────────────────┘
```

- **API 层**：仅负责请求解析、依赖注入、调用编排、返回响应与统一异常/日志。
- **编排层**：定义图结构（节点、边、条件边）、状态类型（`SalesEmailState`）、复跑逻辑（`resume`）。
- **节点层**：每个节点接收当前状态（及可选依赖），返回更新后的状态；不直接依赖 FastAPI。
- **基础设施**：数据库（SQLAlchemy + Alembic）、LangGraph 检查点（PostgreSQL）、外部客户端（Dify、FileServer、MasterData、Mailer）、可观测性（日志、指标、脱敏、健康检查）。

### 1.3 核心抽象

| 抽象 | 位置 | 说明 |
|------|------|------|
| **State** | `graphs/sales_email/state.py` | `SalesEmailState`：Pydantic 模型，承载邮件事件、主数据、匹配结果、Dify/ERP 结果、最终状态、错误/告警、人工审核信息等。所有节点读/写此状态。 |
| **Graph** | `graphs/sales_email/graph.py` | LangGraph `StateGraph(SalesEmailState)`：由 `build_sales_email_graph(...)` 构建，包含节点、边、条件边，编译时绑定 PostgreSQL Checkpointer。 |
| **Repository** | `db/repo.py` | `OrchestratorRepo`：封装 `orchestration_runs`、`idempotency_records`、`audit_events` 的创建/更新/查询，供节点与路由使用。 |
| **Checkpoint** | `db/checkpoint/postgres_checkpoint.py` | `PostgresCheckpointStore`：LangGraph 状态持久化，支持断点续跑与人工审核后从指定节点恢复。 |
| **Settings** | `settings.py` | 唯一配置入口，Pydantic Settings，从环境/`.env` 加载；`extra="ignore"` 忽略未知键。 |
| **OrchestratorError** | `errors.py` | 业务异常，带 `code`、`reason`、`details`；与 HTTP 状态码/错误码映射在路由层处理。 |

---

## 2. 入口点与生命周期

### 2.1 进程入口

- **应用入口**：`src/api/main.py`。
  - 将 `src/` 加入 `sys.path`，便于无包结构下导入 `api`、`db`、`settings` 等。
  - 加载项目根目录下的 `.env`（若存在），并 `Settings.from_env()`。
  - 创建 FastAPI `app`，挂载中间件（RequestId → Logging → Exception → CORS），挂载 `api.routes.router`。
  - `if __name__ == "__main__"` 时使用 **uvicorn** 启动（默认 `0.0.0.0:18000`，注意与 README 中 8000 可能不一致，以代码为准）。

### 2.2 请求生命周期（以 POST /v1/orchestrations/sales-email/run 为例）

1. **中间件**：RequestIdMiddleware 生成/传递 `X-Request-ID`，LoggingMiddleware 记录请求/响应，ExceptionMiddleware 捕获未处理异常并返回 500。
2. **依赖注入**（`api/deps.py`）：按需创建 `Settings`、DB Session、`OrchestratorRepo`、MasterData/FileServer/Dify/Mailer 等客户端（每次请求新建 Session 与部分客户端）。
3. **路由** `run_sales_email`：
   - 生成 `run_id`（UUID），`started_at`（ISO 时间）。
   - 在 DB 中 `repo.create_run(run_id, message_id, PENDING, started_at)`。
   - 创建 `PostgresCheckpointStore` 并 `await checkpoint_store.initialize()`。
   - 调用 `build_sales_email_graph(...)` 得到已编译的图（带 checkpointer）。
   - 构造 `SalesEmailState(email_event=request, started_at=started_at)`，调用 `graph.ainvoke(initial_state.model_dump(), {"configurable": {"thread_id": run_id}})`。
   - 将返回的最终状态转为 `OrchestratorRunResult` 返回；若异常则 `repo.update_run_status(run_id, FAILED)` 并抛出 HTTP 500。
4. **Session**：请求结束时 `get_db_session` 的 `finally` 关闭 session。

### 2.3 图执行生命周期

- **thread_id**：与 `run_id` 一致，用作 LangGraph 的 `configurable.thread_id`，保证一次运行对应一条检查点线程。
- **节点顺序**（概要）：check_idempotency → load_masterdata → match_contact → detect_contract_signal → match_customer → upload_pdf → call_dify_contract → call_dify_order_payload → call_gateway → notify_sales → finalize → END。
- **条件分支**：
  - 若 idempotency 命中且已成功，则直接跳到 finalize。
  - 若联系人未匹配，则跳到 notify_sales 再 finalize。
  - 若非合同邮件，则跳到 finalize。
- **finalize 节点**：确定 `final_status`，必要时写入 `manual_review` 与 redacted `state_json`，并 `repo.update_run_status(run_id, ...)`；`run_id` 来自图执行时的 config（与 thread_id 一致）。

---

## 3. 核心模块及其职责

### 3.1 api/

| 文件 | 职责 |
|------|------|
| `main.py` | 应用入口：路径与 .env 设置、FastAPI 实例、中间件、路由挂载、/healthz、uvicorn 启动。 |
| `routes.py` | 编排 HTTP 端点：`/sales-email/run`、`/sales-email/replay`、`/sales-email/manual-review/submit`、`/healthz`（可调用 observability.monitoring.check_health）。请求/响应使用 schemas 与 mcs_contracts 模型。 |
| `deps.py` | FastAPI 依赖：get_settings、get_db_session、get_repo、get_masterdata_client、get_file_server、get_dify_contract_client、get_dify_order_client、get_mailer。 |
| `schemas.py` | 请求/响应模型：RunRequest=EmailEvent，RunResponse=OrchestratorRunResult，ReplayRequest，ManualReview* 复用 contracts。 |
| `middleware.py` | RequestIdMiddleware、LoggingMiddleware、ExceptionMiddleware。 |

### 3.2 db/

| 文件/目录 | 职责 |
|-----------|------|
| `engine.py` | 同步/异步引擎与 session 工厂（create_db_engine、create_session_factory），供 deps 与 checkpoint 使用。 |
| `models.py` | SQLAlchemy 模型：OrchestrationRun、IdempotencyRecord、AuditEvent。 |
| `repo.py` | OrchestratorRepo：create_run、update_run_status、write_audit_event、get/upsert idempotency、find_run_by_message_id、get_run_with_state、assert_run_in_status、write_manual_review_decision。 |
| `checkpoint/postgres_checkpoint.py` | PostgresCheckpointStore：异步引擎、PostgresSaver、initialize、get_checkpoint_saver_sync/get_checkpoint_saver。 |
| `migrations/` | Alembic 版本与 env，管理表结构变更。 |

### 3.3 graphs/

| 文件/目录 | 职责 |
|-----------|------|
| `registry.py` | GraphRegistry、GraphInfo：按名称/版本注册与获取图（当前 sales_email 未注册到 registry，仅为预留扩展）。 |
| `sales_email/state.py` | SalesEmailState 定义及 add_error、add_warning、set_manual_review 等辅助方法。 |
| `sales_email/graph.py` | build_sales_email_graph：构建 StateGraph，添加节点与边，条件边（idempotency/contact/contract_signal），编译时绑定 checkpointer。 |
| `sales_email/resume.py` | determine_resume_node、resume_from_node；ALLOWED_RESUME_NODES 白名单；人工审核后从某节点恢复并打补丁状态。 |
| `sales_email/nodes/*.py` | 各节点实现：check_idempotency、load_masterdata、match_contact、detect_contract_signal、match_customer、upload_pdf、call_dify_contract、call_dify_order_payload、call_gateway、notify_sales、finalize、generate_candidates、persist_audit 等。 |

### 3.4 tools/

| 文件 | 职责 |
|------|------|
| `dify_client.py` | DifyClient：chatflow 调用、重试、解析 JSON 答案。 |
| `file_server.py` | FileServerClient：上传/下载文件。 |
| `masterdata_client.py` | MasterDataClient：获取主数据（客户、联系人等）。 |
| `mailer.py` | Mailer：发送邮件（如通知销售）。 |
| `similarity.py` | 相似度计算（如 rapidfuzz），供匹配节点使用。 |

### 3.5 observability/

| 文件 | 职责 |
|------|------|
| `logging.py` | setup_logging、get_logger（logger 名 "mcs"），可选 JSON 与 request_id。 |
| `redaction.py` | redact_dict：对敏感字段脱敏，供审计与 state_json 持久化。 |
| `monitoring.py` | check_health（DB、可选 Dify）、get_metrics（Prometheus）。 |
| `metrics.py` | 指标定义（如 dify_calls_total）。 |
| `retry.py` | retry_with_backoff。 |
| `langsmith.py` | LangSmith 追踪集成（若启用）。 |

### 3.6 其他

| 文件 | 职责 |
|------|------|
| `settings.py` | Settings：应用、DB、Dify、FileServer、SMTP、LangSmith、安全、MasterData、Gateway 等配置项。 |
| `errors.py` | 错误码常量与 OrchestratorError。 |
| `templates/*.j2` | Jinja2 邮件模板（manual_review、order_success、order_failed）。 |

---

## 4. 扩展点与安全修改区域

### 4.1 推荐扩展点

| 扩展点 | 位置 | 方式 |
|--------|------|------|
| **新增编排图** | `graphs/<domain>/` | 新建目录，仿照 `sales_email`：定义 state、graph、nodes、resume（若需人工恢复）；在 `api/routes.py` 中新增路由，调用 `build_*_graph` 与 ainvoke。 |
| **新增节点** | `graphs/sales_email/nodes/` | 新增 `node_*.py`，签名 `(state, ...deps) -> state`；在 `graph.py` 中 `add_node` 并加边或条件边。 |
| **新 API 端点** | `api/routes.py` | 新路由函数，通过 deps 注入所需 Repo/Clients；如需新 schema 可在 `api/schemas.py` 或 contracts 中定义。 |
| **新依赖** | `api/deps.py` | 新增 `get_*` 函数，返回客户端或配置；在路由中通过 `Depends(get_*)` 注入。 |
| **图注册** | `graphs/registry.py` | 将新图通过 `GraphInfo` 注册到 `GraphRegistry`，便于网关或统一入口按名称/版本解析。 |
| **健康检查** | `observability/monitoring.py` | 在 `check_health` 中增加对新增依赖服务的探测。 |

### 4.2 安全修改区域（需谨慎）

| 区域 | 说明 |
|------|------|
| **SalesEmailState 字段** | 增删改字段会影响所有节点及 resume、finalize、manual_review 的 state_json；需同步 contracts 与前端/调用方。 |
| **图边与条件边** | 修改 `graph.py` 中边或条件边会改变执行路径与幂等/人工审核语义；需回归测试。 |
| **OrchestratorRepo 事务** | 当前 create_run/update_run_status 等内部 commit；若引入跨表或跨服务事务，需统一事务边界。 |
| **Checkpointer** | 使用 LangGraph 官方 PostgresSaver；不要随意改 checkpoint 表结构或序列化格式。 |
| **errors.py 错误码** | 新增可；修改或删除已有 code 会影响调用方与 manual_review 逻辑。 |

### 4.3 不建议修改

| 区域 | 说明 |
|------|------|
| **main.py 中间件顺序** | 顺序影响 RequestId/日志/异常处理行为，无充分理由勿调换。 |
| **deps 中 Session 生命周期** | 当前「每请求一 Session、finally 关闭」是预期用法，避免改为全局单例 Session。 |

---

## 5. 隐含假设与不变式

### 5.1 假设

- **run_id = thread_id**：一次 `/sales-email/run` 的 `run_id` 作为 LangGraph 的 `configurable.thread_id`，且 finalize 等节点依赖该 config 中的 run_id 写库。
- **DB 与 Checkpoint 共用同一 DB 配置**：`Settings.db_dsn` 既用于 OrchestratorRepo 的同步引擎，也用于 PostgresCheckpointStore 的异步引擎（仅协议改为 `postgresql+asyncpg://`）。
- **请求体即 EmailEvent**：`/sales-email/run` 的 body 能反序列化为 `EmailEvent`（来自 mcs_contracts），且包含 provider、account、message_id、from_email、attachments 等必填字段。
- **人工审核**：仅当 `final_status == MANUAL_REVIEW` 时，会写入 manual_review 候选并依赖后续 `/sales-email/manual-review/submit` 提交决策；RESUME 时从 `ALLOWED_RESUME_NODES` 中某一节点恢复。
- **幂等键**：由 message_id + file_sha256 + customer_id 等派生，在 check_idempotency 及后续节点中可能短路或复用已有结果。

### 5.2 不变式

- **State 为 Pydantic 模型**：所有节点接收和返回的 state 可序列化为 `SalesEmailState.model_dump()`，且与 LangGraph 的 state 类型一致。
- **Result 模型**：工具/节点对外结果使用 contracts 中的 Result 模型（如 `ContactMatchResult`、`OrchestratorRunResult`），且含 `ok` 等约定字段。
- **错误码**：业务失败使用 `OrchestratorError` 或 state.errors 中的 `ErrorInfo`，带稳定 `code`，便于前端/网关映射。
- **审计与脱敏**：写入 `audit_events` 或 `state_json` 前使用 `redact_dict` 脱敏敏感字段。

---

## 6. 新功能的集成方式

### 6.1 新增一种「销售邮件」后的新业务流程（新图）

1. 在 `graphs/` 下新建目录，如 `graphs/other_flow/`。
2. 定义 `state.py`（如 `OtherFlowState`）、`graph.py`（`build_other_flow_graph`）、`nodes/` 下各节点。
3. 在 `api/routes.py` 中挂载新路由（如 `POST /v1/orchestrations/other-flow/run`），在路由内创建 checkpoint store、调用 `build_other_flow_graph`、构造初始状态并 `ainvoke`。
4. 若需人工审核或复跑，可参考 `sales_email` 的 resume 与 manual-review 端点实现。

### 6.2 在现有 sales_email 图中增加一个节点

1. 在 `graphs/sales_email/nodes/` 下新增 `node_xxx.py`，实现 `async def node_xxx(state, ...) -> SalesEmailState`。
2. 在 `graph.py` 中：`graph.add_node("xxx", lambda s: node_xxx(s, ...))`，并在合适位置 `add_edge` 或 `add_conditional_edges`。
3. 若节点依赖新外部服务，在 `api/deps.py` 中增加 `get_xxx_client`，并在 `build_sales_email_graph` 中增加参数，由 routes 传入。

### 6.3 新增或调整配置项

1. 在 `settings.py` 的 `Settings` 中增加字段（含默认值）。
2. 在 `.env` 或环境中提供值；若希望忽略未知键，已使用 `extra="ignore"`。
3. 在 deps 或节点中通过 `Settings` 读取新配置。

---

## 7. 接口调用示例

### 7.1 启动一次销售邮件编排（Run）

```http
POST /v1/orchestrations/sales-email/run
Content-Type: application/json
X-Request-ID: optional-uuid
X-API-Key: <optional>

{
  "provider": "imap",
  "account": "user@example.com",
  "folder": "INBOX",
  "uid": "42",
  "message_id": "<msg-id@example.com>",
  "from_email": "sender@example.com",
  "to": ["sales@example.com"],
  "cc": [],
  "subject": "Contract PDF",
  "body_text": "Please see attachment.",
  "body_html": null,
  "received_at": "2026-01-29T10:00:00Z",
  "attachments": [
    {
      "attachment_id": "file1.pdf",
      "filename": "file1.pdf",
      "content_type": "application/pdf",
      "size": 1024,
      "sha256": "...",
      "bytes_b64": "..."
    }
  ]
}
```

**响应**（成功时，body 为 `OrchestratorRunResult`）：

```json
{
  "run_id": "uuid",
  "message_id": "<msg-id@example.com>",
  "status": "SUCCESS",
  "started_at": "2026-01-29T10:00:00Z",
  "finished_at": "2026-01-29T10:00:05Z",
  "idempotency_key": "...",
  "customer_id": "...",
  "contact_id": "...",
  "file_url": "...",
  "sales_order_no": "...",
  "order_url": "...",
  "warnings": [],
  "errors": []
}
```

### 7.2 按 message_id 复播（Replay）

```http
POST /v1/orchestrations/sales-email/replay
Content-Type: application/json

{
  "message_id": "<msg-id@example.com>"
}
```

返回该 message_id 最近一次运行的 `OrchestratorRunResult`（来自 DB）。

### 7.3 人工审核提交（Manual Review Submit）

```http
POST /v1/orchestrations/sales-email/manual-review/submit
Content-Type: application/json

{
  "run_id": "uuid-from-run",
  "message_id": "<msg-id@example.com>",
  "decision": {
    "action": "RESUME",
    "selected_customer_id": "cust-001",
    "selected_contact_id": "cont-001",
    "selected_attachment_id": "file1.pdf",
    "comment": null
  },
  "operator": { "user_id": "u1", "user_name": "Operator" },
  "auth": { "tenant_id": "t1", "scopes": ["mcs:sales_email:manual_review"], "request_id": "..." }
}
```

- `action` 可为 `RESUME` 或 `BLOCK`；BLOCK 时需 `comment`。
- 服务端会校验 run 状态为 MANUAL_REVIEW、message_id 一致、tenant_id/scopes，然后写审计、更新状态，RESUME 时从 `determine_resume_node` 决定的节点恢复执行。

### 7.4 健康检查

```http
GET /healthz
```

根路径简单返回 `{"status": "ok"}`。若路由中 `/v1/orchestrations/healthz` 使用 `check_health`，则返回带 `checks`（如 database、dify）的详细结构。

---

## 文档版本与维护

- 本文档基于当前 `mcs-orchestrator` 代码目录分析生成。
- 大版本或架构变更时请同步更新本文档（尤其是 1.2 分层图、3 核心模块表、5 假设与不变式、7 接口示例）。
