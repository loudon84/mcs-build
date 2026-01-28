外部系统 / UI / Mailbot
        ↓
[ NestJS Gateway ]        ← 权限 / policy / 路由 / 限流
        ↓
[ LangServe Orchestrator ]← LangGraph 编排 / 状态机
        ↓
[ mcs-erp-gateway ]       ← ERP 协议适配 / 幂等 / 重试 / 错误映射
        ↓
      ERP



核心定位

MCS 的 Edge / BFF / Policy Enforcement Point

它必须做的事（不能下放）

身份与租户识别

JWT 校验

解析 tenant_id / user_id / scopes

策略（policy）执行

哪个 tenant 能用哪些 graph

允许哪些 graph version

限流（tenant + graph）

是否允许触发 MANUAL_REVIEW / RESUME

路由与版本选择

/orchestrations/:graph/run

解析并注入 X-MCS-Graph-Version

审计字段注入（但不存储）

X-MCS-Tenant-ID

X-MCS-User-ID

X-Request-ID

错误规范化

401 / 403 / 429 / 5xx

不暴露内部异常结构

它不应该做的事

❌ 不解析业务 payload

❌ 不调用 ERP

❌ 不理解“销售订单”结构

❌ 不做 LangGraph 状态机