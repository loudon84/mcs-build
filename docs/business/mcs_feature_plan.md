````markdown
# MANUAL_REVIEW 人机协同契约（HITL Contract Spec）
> 适用范围：MCS 平台层（LangGraph 编排 + LangServe 服务化 + DB 审计/幂等）。  
> 目标：当自动链路进入 `MANUAL_REVIEW` 状态时，提供**标准化的候选列表、确认输入、回调接口、恢复节点**以及**权限/审计字段**，保证可控、可追责、可恢复。

---

## 0. 术语与约定

- **Run**：一次编排执行实例（`run_id` 唯一）
- **Manual Review**：需要人工确认后才能继续的状态（`status=MANUAL_REVIEW`）
- **Decision**：人工确认结果（选择客户/联系人/附件/阻断原因）
- **Resume**：从指定节点继续执行（LangGraph resume）
- **权限字段**：由 NestJS 网关注入，Python 不做裁剪，只记录与校验存在性

**时间格式**：ISO8601，含时区  
**字符编码**：UTF-8  
**ID 规则**：所有 *_id 作为字符串，避免 ERP/CRM 不同格式冲突

---

## 1. 场景触发与进入 MANUAL_REVIEW 的标准原因（Reason Codes）

### 1.1 触发条件（至少满足其一）
- `CONTACT_NOT_FOUND`：发件人邮箱未命中 `contacts.email`
- `CUSTOMER_MATCH_LOW_SCORE`：附件名与客户相似度低于阈值（例如 <75）
- `CUSTOMER_CONTACT_MISMATCH`：联系人 customer_id 与客户匹配结果不一致
- `MULTI_PDF_ATTACHMENTS`：同一邮件存在多个 PDF，需人工选择“哪个是合同”
- `MULTI_CUSTOMER_AMBIGUOUS`：top candidates 分数接近且无法自动判定
- `FILE_ACCESS_BLOCKED`：文件 URL Dify 不可达/鉴权限制（需人工选择替代文件/重传）

### 1.2 必须落库字段
- `run_id`
- `message_id`
- `manual_review.reason_code`
- `manual_review.created_at`

---

## 2. Step-A：生成候选客户列表（Candidate Customers）

> 本步骤由编排图在进入 `MANUAL_REVIEW` 前生成，并持久化到 `audit_events` + `orchestration_runs.state_json`（脱敏后）。

### 2.1 输入（Input）
```json
{
  "run_id": "string",
  "message_id": "string",
  "from_email": "string",
  "pdf_candidates": [
    { "attachment_id": "string", "filename": "string", "sha256": "string", "size": 123 }
  ],
  "customers": [
    { "customer_num": "string", "customer_id": "string", "customer_name": "string" }
  ],
  "contacts_hit": {
    "matched": true,
    "contact": { "contact_id": "string", "email": "string", "name": "string", "customer_id": "string" }
  },
  "threshold": 75
}
````

### 2.2 输出（Output）

```json
{
  "ok": true,
  "reason_code": "CUSTOMER_MATCH_LOW_SCORE|CUSTOMER_CONTACT_MISMATCH|MULTI_PDF_ATTACHMENTS|CONTACT_NOT_FOUND|MULTI_CUSTOMER_AMBIGUOUS|FILE_ACCESS_BLOCKED",
  "candidates": {
    "pdfs": [
      {
        "attachment_id": "string",
        "filename": "string",
        "sha256": "string",
        "size": 123,
        "suggested": true
      }
    ],
    "customers": [
      {
        "customer_id": "string",
        "customer_num": "string",
        "customer_name": "string",
        "score": 88,
        "evidence": {
          "matched_tokens": ["string"],
          "filename_normalized": "string"
        },
        "suggested": true
      }
    ],
    "contacts": [
      {
        "contact_id": "string",
        "name": "string",
        "email": "string",
        "telephone": "string",
        "customer_id": "string",
        "suggested": true
      }
    ]
  },
  "constraints": {
    "require_customer_selection": true,
    "require_pdf_selection": true,
    "max_candidates": 3
  },
  "next_actions": [
    "SELECT_CUSTOMER",
    "SELECT_CONTACT",
    "SELECT_PDF",
    "BLOCK_AUTOMATION"
  ]
}
```

### 2.3 规则（Constraints）

* `candidates.customers` 默认返回 top3（可配置）
* `suggested=true` 只能标记 0 或 1 个，避免 UI 误导
* `evidence` 必须可解释（至少提供 normalized filename 或 matched_tokens）
* **脱敏**：`telephone/email` 可在候选里保留，但写日志/trace 时必须 mask

---

## 3. Step-B：确认输入契约（Manual Review Decision Input）

> 人工确认由 UI/销售邮件回复/工单系统完成。最终都必须落为统一结构，供 API 回调。

### 3.1 输入（Decision Input）

```json
{
  "run_id": "string",
  "message_id": "string",
  "decision": {
    "action": "RESUME|BLOCK",
    "selected_customer_id": "string",
    "selected_contact_id": "string",
    "selected_attachment_id": "string",
    "override": {
      "customer_num": "string",
      "po_number": "string"
    },
    "comment": "string"
  },
  "operator": {
    "user_id": "string",
    "user_name": "string",
    "department": "string"
  },
  "auth": {
    "tenant_id": "string",
    "scopes": ["string"],
    "request_id": "string"
  }
}
```

### 3.2 字段要求（Required Fields）

* `run_id` 必填
* `decision.action` 必填
* 当 `action=RESUME`：

  * `selected_customer_id` 必填
  * `selected_attachment_id` 必填（若存在多 PDF/未自动选定）
  * `selected_contact_id`：若 `CONTACT_NOT_FOUND`，允许为空（后续进入“补联系人”分支或阻断）
* 当 `action=BLOCK`：

  * `comment` 必填（用于审计：为何阻断）

### 3.3 允许的 Override（谨慎）

* `override.customer_num` 仅用于显示/报文辅助，不应替代 `selected_customer_id`
* `override.po_number` 可用于 Dify 合同识别提示（提升识别稳定性）

---

## 4. Step-C：确认回调接口（Manual Review Callback API）

> 由 NestJS 网关调用 LangServe（或 Python API），完成决策写入并触发 resume。

### 4.1 Endpoint

* `POST /v1/orchestrations/sales-email/manual-review/submit`

### 4.2 Request（同 3.1）

```json
{
  "run_id": "string",
  "message_id": "string",
  "decision": { ... },
  "operator": { ... },
  "auth": { ... }
}
```

### 4.3 Response

成功提交并触发继续：

```json
{
  "ok": true,
  "status": "RESUMING",
  "resume": {
    "from_node": "string",
    "planned_path": ["string"]
  },
  "audit_id": "string",
  "run_id": "string"
}
```

成功提交但被阻断：

```json
{
  "ok": true,
  "status": "BLOCKED",
  "final_status": "MANUAL_REVIEW",
  "audit_id": "string",
  "run_id": "string"
}
```

失败：

```json
{
  "ok": false,
  "error_code": "RUN_NOT_FOUND|INVALID_DECISION|PERMISSION_DENIED|RUN_NOT_IN_MANUAL_REVIEW|STALE_DECISION",
  "reason": "string"
}
```

### 4.4 校验规则（Server-side Validation）

* `run_id` 必须存在
* 当前 `run.status` 必须为 `MANUAL_REVIEW`
* `message_id` 若提供则必须与 run 中一致（防串单）
* `auth.tenant_id` 必须与 run 的 tenant_id 一致（防跨租户）
* `scopes` 至少包含：`mcs:sales_email:manual_review`（可按你们权限体系映射）
* 决策必须引用候选集中的 id（除非允许 override 的白名单字段）

---

## 5. Step-D：恢复节点与 Resume 契约（Resume Node Contract）

> Resume 的关键是：**从“可恢复节点”继续**，避免重复上传/重复下单。

### 5.1 可恢复节点清单（Allowed Resume Nodes）

* `node_match_customer`（当客户选择改变）
* `node_upload_pdf`（当选择的附件改变且未上传）
* `node_call_dify_contract`（当 file_url/customer_id 改变）
* `node_call_dify_order_payload`（当客户/联系人/合同明细变更）
* `node_call_erp_gateway`（仅当幂等检查确保不会重复下单）

> 不允许从 `node_load_masterdata` 之前恢复（避免状态重置），也不允许跳过幂等检查。

### 5.2 Resume 输入（Internal Resume Input）

```json
{
  "run_id": "string",
  "resume_from_node": "string",
  "patch": {
    "selected_customer_id": "string",
    "selected_contact_id": "string",
    "selected_attachment_id": "string"
  },
  "operator": {
    "user_id": "string",
    "request_id": "string"
  }
}
```

### 5.3 Resume 输出（Internal Resume Output）

```json
{
  "ok": true,
  "run_id": "string",
  "status": "RUNNING",
  "resumed_from": "string",
  "updated_state_version": 2
}
```

### 5.4 Patch 规则

* patch 只能修改以下 state 字段（白名单）：

  * `matched_customer`
  * `matched_contact`
  * `pdf_attachment`（selected）
  * `manual_review.decision`
* patch 修改后必须重新计算：

  * `idempotency_key`（若 customer_id 或 file_sha256 变化）
* 若 `idempotency_key` 命中 SUCCESS，必须直接短路到 `node_notify_sales`

---

## 6. 权限与审计字段（必须贯穿）

### 6.1 网关注入字段（Python 必须记录但不裁剪）

* `tenant_id`
* `user_id`
* `scopes`
* `request_id`

### 6.2 DB 审计落库要求

1. `audit_events`（每次人工提交至少写 1 条）

* step: `manual_review_submit`
* payload_json（脱敏）必须包含：

  * `run_id/message_id`
  * `reason_code`
  * `decision.action`
  * `selected_customer_id/selected_attachment_id/selected_contact_id`
  * `operator.user_id`
  * `auth.tenant_id/request_id`

2. `orchestration_runs`（更新）

* status 保持 `MANUAL_REVIEW`（若 BLOCK）或进入 `RUNNING`（若 RESUME）
* state_json 写入 `manual_review` 结构（脱敏）

3. `idempotency_records`（如涉及 resume 造成 key 变化）

* 写入新记录或更新状态水位
* 必须保留旧 key 的引用（便于追踪）

### 6.3 脱敏规则（最小要求）

* email：mask `a***@domain.com`
* telephone：mask 中间 4 位
* unit_price/amount：日志与 trace 中可四舍五入/范围化（按合规要求）
* file_url：仅保留域名+file_id，路径截断

---

## 7. 状态结构补充（写入 SalesEmailState.manual_review）

> 以下结构必须加入 `SalesEmailState`，用于统一恢复与审计。

```json
{
  "manual_review": {
    "reason_code": "string",
    "created_at": "datetime",
    "candidates": { "customers": [], "contacts": [], "pdfs": [] },
    "decision": {
      "action": "RESUME|BLOCK",
      "selected_customer_id": "string",
      "selected_contact_id": "string",
      "selected_attachment_id": "string",
      "comment": "string",
      "decided_at": "datetime",
      "operator_user_id": "string",
      "request_id": "string"
    }
  }
}
```

---

## 8. Cursor 代码落地文件清单（对应执行计划骨架）

> 以下文件需要新增/补齐（按你们现有目录规范）。

1. `services/mcs-orchestrator/src/mcs_orchestrator/api/routes.py`

* TODO: 新增 `POST /v1/orchestrations/sales-email/manual-review/submit`

2. `services/mcs-orchestrator/src/mcs_orchestrator/schemas.py`

* TODO: 新增 `ManualReviewSubmitRequest/Response` Pydantic models（复用 contracts）

3. `libs/contracts/src/mcs_contracts/orchestrator.py`

* TODO: 扩展 `StatusEnum` 与 `OrchestratorRunResult` 以包含 `manual_review` 摘要（可选）

4. `services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/state.py`

* TODO: 增加 `manual_review` 字段结构（如第 7 节）

5. `services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/finalize.py`

* TODO: 当 status=MANUAL_REVIEW 时输出候选摘要并持久化

6. `services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/persist_audit.py`

* TODO: 支持 step=`manual_review_submit` 的审计写入

7. `services/mcs-orchestrator/src/mcs_orchestrator/db/repo.py`

* TODO:

  * `write_manual_review_decision(run_id, decision_payload)`
  * `assert_run_in_status(run_id, MANUAL_REVIEW)`
  * `update_run_status(run_id, RUNNING/BLOCKED)`

8. `services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/graph.py`

* TODO: 提供 `resume_from_node` 的入口（或在 API 中调用 graph 的 resume handler）

9. `services/mcs-orchestrator/tests/test_manual_review_flow.py`

* TODO: 测试：

  * 进入 MANUAL_REVIEW 生成候选
  * 提交 RESUME 后从正确节点继续并最终 SUCCESS
  * 提交 BLOCK 后保持 MANUAL_REVIEW 且审计存在
  * 权限字段缺失/tenant 不一致返回 PERMISSION_DENIED

---

## 9. 验收标准（Definition of Done）

* 能稳定触发 `MANUAL_REVIEW`（至少覆盖：低相似度、联系人不一致、多 PDF）
* 能通过 `manual-review/submit` 提交决策
* 能从允许节点恢复执行，不重复创建订单（幂等生效）
* DB 审计完整：能追溯“谁在什么时候选了哪个客户/附件/联系人”
* trace/log 脱敏符合要求

```

::contentReference[oaicite:0]{index=0}
```
