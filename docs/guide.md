关键模块说明（按你要求的概念映射）
1) Agent

落地位置：agent-runtime/src/graphs/*

形式：LangGraph 图（节点是能力、边是控制流）

特点：Agent 不应该“直接操作系统”，而应通过 Skills/Tools 执行

2) Context

落地位置：control-plane/src/context/ + indexer/

内容：代码片段、相关文档、依赖图、变更历史、运行数据快照（可选）

原则：Context 必须“可引用、可审计、可复现”（避免凭空编）

3) Memories

落地位置：agent-runtime/src/memory/ + docs/adr + KB

例子：历史坑、合规红线、模块 owner、关键表语义、已知回归点

原则：Memory 是资产，不是聊天记录

4) Rules

落地位置：control-plane/src/policy/（强治理） + agent-runtime/src/rules/（轻校验）

例子：

“涉及过账/冲销只能走高风险 Skill + 需要人工确认 token”

“生产环境禁止自动跑 destructive migration”

5) Command

落地位置：通常是 Control Plane 下发的“标准动作指令”，或 IDE/CLI 侧的命令封装

建议：将 Command 映射到 Skills（Command 是入口，Skill 是执行最小单元）

6) Index & Docs

落地位置：indexer/ + docs/

作用：让 Context 构建不靠“猜”，靠“可检索证据”

7) Tools

落地位置：mcp/（推荐）或 skills/（更强治理）

区别：

Tool：能力接口（可能比较自由）

Skill：批准过的最小动作（强约束、强审计）

8) MCP

落地位置：mcp/servers/*

作用：把 ERP/Repo/Docs/DB 等系统能力用标准协议暴露给 Agent

9) Skills

落地位置：skills/src/* + skills/manifests/*.yaml

作用：高风险 ERP 操作必须 Skill 化（白名单、审批、审计、回滚）