# Sales Email 图说明

本文档说明 `sales_email` LangGraph 的目录结构、节点流程以及修改流程顺序的方法。

---

## 1. 目录与入口

- **图定义**：本目录下的 `graph.py`（`build_sales_email_graph`）
- **状态**：`state.py`（`SalesEmailState`）
- **节点实现**：`nodes/*.py`，在 `nodes/__init__.py` 中导出，在 `graph.py` 中通过 wrapper 注入依赖并 `add_node`
- **流程顺序**：完全由 `graph.py` 中的 **`add_edge` / `add_conditional_edges` / `set_entry_point`** 决定

---

## 2. 节点流程概览

整体是：**一个入口 → 若干条件分支 → 一条主链路（线性）→ 结束**。

### 2.1 入口与第一处分支

- **入口**：`set_entry_point("check_idempotency")`，即 START → `check_idempotency`
- **第一处条件边**：
  - 若 `final_status == SUCCESS` 且 `erp_result.ok`：→ **finalize**（幂等命中，直接结束）
  - 否则：→ **load_masterdata**，进入主流程

### 2.2 主流程线性链（在未提前结束的情况下）

顺序为：

1. **load_masterdata** — 加载主数据
2. **match_contact** — 按发件人邮箱匹配联系人
3. **detect_contract_signal** — 当前入口直接返回通过状态（`contract_signals.ok=True`, `is_contract_mail=True`），始终进入主链
4. **match_customer** — 匹配客户
5. **call_dify_contract** — 调用 Dify 合同解析
6. **call_dify_order_payload** — 调用 Dify 订单 payload
7. **call_gateway** — 当前不启用，仅透传 state（不调用 ERP 网关）
8. **upload_pdf** — 上传 PDF（已调到 call_gateway 之后）
9. **notify_sales** — 通知销售
10. **finalize** — 写库、更新运行状态
11. **END**

### 2.3 中间两处「提前结束」的条件边

- **match_contact 之后**（`should_continue_after_contact`）
  - 若 `matched_contact` 存在且 `not matched_contact.ok`：→ **notify_sales**（联系人未匹配，跳过后面的合同/客户/Dify/ERP，直接通知销售再 finalize）
  - 否则：→ **detect_contract_signal**（继续主流程）

- **detect_contract_signal 之后**（`should_continue_after_signal`）
  - 当前实现下入口直接返回通过状态，故 `is_contract_mail=True`，始终 → **match_customer**
  - 若将来恢复原有逻辑：`not contract_signals.is_contract_mail` → **finalize**，否则 → **match_customer**

### 2.4 流程简图

```
START
  → check_idempotency
       ├─ [已成功且 erp_result.ok] → finalize → END
       └─ [否则] → load_masterdata
                        → match_contact
                             ├─ [联系人未匹配] → notify_sales → finalize → END
                             └─ [否则] → detect_contract_signal
                                            ├─ [非合同邮件] → finalize → END
                                            └─ [否则] → match_customer
                                                           → call_dify_contract
                                                           → call_dify_order_payload
                                                           → call_gateway（不启用，透传）
                                                           → upload_pdf
                                                           → notify_sales
                                                           → finalize
                                                           → END
```

---

## 3. 修改流程顺序的方法

所有「顺序」都只在 **`graph.py`** 里通过边和入口来改，不动节点内部逻辑也能调整流程。

### 3.1 改入口

- 当前：`graph.set_entry_point("check_idempotency")`
- 若要从别的节点开始（例如跳过幂等或从 `load_masterdata` 开始）：把 `set_entry_point("节点名")` 改成目标节点；从中间节点开始时，前面节点不会执行，state 里对应字段需由调用方预先注入或接受为 None。

### 3.2 改线性主链顺序

主链由一串 **`add_edge(A, B)`** 决定，例如：

```python
graph.add_edge("load_masterdata", "match_contact")
graph.add_edge("match_contact", "detect_contract_signal")
graph.add_edge("detect_contract_signal", "match_customer")
graph.add_edge("match_customer", "call_dify_contract")
graph.add_edge("call_dify_contract", "call_dify_order_payload")
graph.add_edge("call_dify_order_payload", "call_gateway")
graph.add_edge("call_gateway", "upload_pdf")
graph.add_edge("upload_pdf", "notify_sales")
# ...
```

要改顺序就改这些边，例如：

- 若希望 **先 match_customer 再 match_contact**：把 `load_masterdata` 的下一跳从 `match_contact` 改成 `match_customer`，再在 `match_customer` 后连 `match_contact`，并相应调整后面一条边；需注意当前 `match_contact` 依赖 `masterdata`，`match_customer` 可能依赖联系人等，调换后要在节点实现或 state 上保证数据已就绪。
- 若希望 **先 upload_pdf 再 match_customer**：把 `detect_contract_signal` → `match_customer` 改为 `detect_contract_signal` → `upload_pdf`，再 `upload_pdf` → `match_customer`，并检查 `match_customer` 是否依赖 PDF 上传结果。

原则：**谁先执行就谁在前面的 `add_edge(前, 后)` 里**；只改边的先后关系即可，无需改节点函数签名。

### 3.3 改条件分支（提前结束 / 跳转）

- **幂等后的分支**：改 `should_skip_after_idempotency` 的返回值及 `add_conditional_edges("check_idempotency", ..., {"finalize": "finalize", "load_masterdata": "load_masterdata"})` 中的 key，或增加新的目标节点（如先到 `notify_sales` 再 finalize）。
- **match_contact 后**：改 `should_continue_after_contact` 的逻辑或返回的 key，以及 `add_conditional_edges("match_contact", ...)` 的 map；例如希望「联系人未匹配时先打审计再通知」，可改为返回 `"persist_audit"` 并在 map 里指向 `persist_audit`，再在 `persist_audit` 后连 `notify_sales`。
- **detect_contract_signal 后**：同理改 `should_continue_after_signal` 和对应的 `add_conditional_edges` 的 map。

只要条件函数返回的 key 在 map 里存在，就会跳到对应节点；**不要**对同一源节点既 `add_edge(源, 某节点)` 又 `add_conditional_edges(源, ...)` 到同一或重叠目标，否则容易触发「重复静态边+条件边」导致的并发更新问题（参见项目 LangGraph 规则）。

### 3.4 插入或删除节点

- **插入**：在 `graph.py` 里 `add_node("新节点", wrapper)`，然后在合适位置用 `add_edge(前, "新节点")` 和 `add_edge("新节点", 后)` 串进主链或某条分支。
- **删除**：去掉该节点的 `add_node`，并把原来指向它的边改为指向它的下一跳（或改为条件边到其它节点）。

### 3.5 与 resume 的关系

`resume.py` 里的 `determine_resume_node` / `resume_from_node` 会按「断点」决定从哪个节点继续。若改了图的顺序或节点名，需确认 resume 逻辑里依赖的节点名、状态字段是否仍与新区一致，否则手动恢复/重试时可能从错误节点继续。

---

## 4. 小结

- **流程**：入口 `check_idempotency` → 条件到 finalize 或 `load_masterdata` → 主链 10 个节点线性执行（其中 **detect_contract_signal** 入口直接返回通过、**call_gateway** 不启用），中间在 `match_contact`、`detect_contract_signal` 两处可提前跳到 `notify_sales` 或 `finalize`。**upload_pdf** 已调到 **call_gateway** 之后。
- **改顺序**：在 `graph.py` 里改 `set_entry_point`、`add_edge` 和 `add_conditional_edges` 即可；不动 `nodes/` 里的实现也能调整顺序，只要保证每个节点拿到的 state 已由前面的节点或输入准备好。
