---
name: MANUAL_REVIEW 人机协同契约实施
overview: 实现 MANUAL_REVIEW 人机协同契约功能，包括候选生成、决策提交 API、Resume 恢复执行、审计追踪和权限校验。
todos:
  - id: contracts-extension
    content: 扩展 contracts：新增错误码、ManualReview 相关模型、扩展 StatusEnum
    status: completed
  - id: state-extension
    content: 扩展 SalesEmailState：添加 manual_review 字段结构
    status: completed
    dependencies:
      - contracts-extension
  - id: nodes-enhancement
    content: 增强节点：detect_contract_signal（多PDF检测）、match_customer（多候选模糊检测）、finalize（候选生成）
    status: completed
    dependencies:
      - state-extension
  - id: candidates-generation
    content: 实现候选生成函数：generate_manual_review_candidates()
    status: completed
    dependencies:
      - nodes-enhancement
  - id: repo-extension
    content: 扩展 Repository：assert_run_in_status、write_manual_review_decision、get_run_with_state
    status: completed
  - id: resume-implementation
    content: 实现 Resume 功能：resume_from_node、state patch、idempotency 重新计算
    status: completed
    dependencies:
      - repo-extension
      - state-extension
  - id: api-manual-review
    content: 实现 Manual Review API：POST /v1/orchestrations/sales-email/manual-review/submit
    status: completed
    dependencies:
      - resume-implementation
      - contracts-extension
  - id: audit-enhancement
    content: 增强审计：支持 manual_review_submit step、完善脱敏规则
    status: completed
    dependencies:
      - api-manual-review
  - id: error-codes
    content: 扩展错误码：MULTI_PDF_ATTACHMENTS、MULTI_CUSTOMER_AMBIGUOUS、FILE_ACCESS_BLOCKED 等
    status: completed
  - id: tests-manual-review
    content: 编写测试用例：覆盖所有 MANUAL_REVIEW 场景和 Resume 流程
    status: completed
    dependencies:
      - api-manual-review
      - audit-enhancement
---

#MANUAL_REVIEW 人机协同契约实施计划

## 概述

根据 `mcs_feature_plan.md` 文档，需要实现完整的人机协同（HITL）流程，当编排进入 `MANUAL_REVIEW` 状态时，提供候选列表生成、决策提交、恢复执行和审计追踪功能。

## 功能增改清单

### 1. Contracts 层扩展

**文件**: `mcs-platform/libs/contracts/src/mcs_contracts/common.py`

- 新增错误码：`MULTI_PDF_ATTACHMENTS`, `MULTI_CUSTOMER_AMBIGUOUS`, `FILE_ACCESS_BLOCKED`
- 新增 `RUNNING` 状态到 `StatusEnum`

**文件**: `mcs-platform/libs/contracts/src/mcs_contracts/orchestrator.py`

- 新增 `ManualReviewCandidates` 模型（包含 customers, contacts, pdfs）
- 新增 `ManualReviewDecision` 模型
- 新增 `ManualReviewSubmitRequest` 模型
- 新增 `ManualReviewSubmitResponse` 模型
- 扩展 `OrchestratorRunResult` 添加 `manual_review` 摘要字段（可选）

### 2. State 层扩展

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/state.py`

- 在 `SalesEmailState` 中添加 `manual_review: Optional[ManualReviewInfo]` 字段
- 新增 `ManualReviewInfo` 内部模型（包含 reason_code, created_at, candidates, decision）

### 3. 节点层增强

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/detect_contract_signal.py`

- 检测多 PDF 场景：当存在多个 PDF 时，设置 `MULTI_PDF_ATTACHMENTS` 并进入 MANUAL_REVIEW
- 保留所有 PDF 候选供人工选择

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/match_customer.py`

- 检测多候选模糊场景：当 top candidates 分数接近（差值 < 5）时，设置 `MULTI_CUSTOMER_AMBIGUOUS`
- 确保 `top_candidates` 包含完整的 evidence（matched_tokens, filename_normalized）

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/finalize.py`

- 当进入 MANUAL_REVIEW 时，调用候选生成函数
- 持久化候选列表到 `state_json`（脱敏后）
- 写入 `manual_review.reason_code` 和 `created_at`

**新增文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/generate_candidates.py`

- 实现 `generate_manual_review_candidates()` 函数
- 生成客户、联系人、PDF 候选列表
- 标记 `suggested` 字段（只能有一个为 true）
- 计算 evidence（matched_tokens, filename_normalized）

### 4. API 层新增

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/api/routes.py`

- 新增 `POST /v1/orchestrations/sales-email/manual-review/submit` 端点
- 实现校验逻辑：
- run_id 存在性检查
- status 必须为 MANUAL_REVIEW
- message_id 一致性检查
- tenant_id 一致性检查（如果 run 中有 tenant_id）
- scopes 权限检查（至少包含 `mcs:sales_email:manual_review`）
- 决策字段引用候选集验证
- 调用 resume 逻辑或标记为 BLOCKED

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/api/schemas.py`

- 新增 `ManualReviewSubmitRequest`（复用 contracts 模型）
- 新增 `ManualReviewSubmitResponse`（复用 contracts 模型）

### 5. Repository 层扩展

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/db/repo.py`

- 新增 `assert_run_in_status(run_id: str, expected_status: str)` 方法
- 新增 `write_manual_review_decision(run_id: str, decision_payload: dict)` 方法
- 新增 `get_run_with_state(run_id: str)` 方法（返回包含 state_json 的 run）
- 扩展 `update_run_status` 支持 `RUNNING` 状态

### 6. Resume 功能实现

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/graph.py`

- 新增 `resume_from_node()` 函数
- 实现节点白名单验证（只允许从指定节点恢复）
- 实现 state patch 逻辑（更新 matched_customer, matched_contact, pdf_attachment）
- 重新计算 idempotency_key（如果 customer_id 或 file_sha256 变化）
- 检查 idempotency 命中，如果命中 SUCCESS 则短路到 notify_sales

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/api/routes.py`

- 在 `manual-review/submit` 中调用 resume 逻辑
- 根据 decision.action（RESUME/BLOCK）执行不同分支

### 7. 审计增强

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/graphs/sales_email/nodes/persist_audit.py`

- 支持 `step="manual_review_submit"` 的审计写入
- 确保 payload_json 包含所有必需字段（脱敏后）

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/observability/redaction.py`

- 增强脱敏规则：
- email: `a***@domain.com` 格式
- telephone: mask 中间 4 位
- file_url: 仅保留域名+file_id

### 8. 错误码扩展

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/errors.py`

- 新增：`MULTI_PDF_ATTACHMENTS`, `MULTI_CUSTOMER_AMBIGUOUS`, `FILE_ACCESS_BLOCKED`
- 新增：`RUN_NOT_IN_MANUAL_REVIEW`, `INVALID_DECISION`, `STALE_DECISION`, `PERMISSION_DENIED`

### 9. 测试用例

**新增文件**: `mcs-platform/services/mcs-orchestrator/tests/test_manual_review_flow.py`

- 测试进入 MANUAL_REVIEW 生成候选
- 测试提交 RESUME 后从正确节点继续并最终 SUCCESS
- 测试提交 BLOCK 后保持 MANUAL_REVIEW 且审计存在
- 测试权限字段缺失/tenant 不一致返回 PERMISSION_DENIED
- 测试多 PDF 场景
- 测试多候选模糊场景
- 测试 resume 时的 idempotency 检查

### 10. 数据库模型扩展（如需要）

**文件**: `mcs-platform/services/mcs-orchestrator/src/mcs_orchestrator/db/models.py`

- 检查 `OrchestrationRun` 是否需要添加 `tenant_id` 字段（用于权限校验）

## 实施顺序

1. **Phase 1**: Contracts 和 State 扩展（基础数据结构）
2. **Phase 2**: 节点层增强（触发条件和候选生成）
3. **Phase 3**: Repository 和 Resume 功能
4. **Phase 4**: API 接口实现
5. **Phase 5**: 审计和脱敏增强
6. **Phase 6**: 测试用例

## 关键设计决策

- **候选生成时机**：在 `finalize` 节点检测到 MANUAL_REVIEW 时生成
- **Resume 节点白名单**：`node_match_customer`, `node_upload_pdf`, `node_call_dify_contract`, `node_call_dify_order_payload`, `node_call_erp_gateway`
- **权限校验**：由 NestJS 网关提供 tenant_id/user_id/scopes，Python 只做记录和校验存在性