关键词都在这里

Control Plane（控制面）：负责“谁能调用什么、在什么条件下调用、如何路由、如何审计、如何灰度”，它不做推理，只做治理与编排。

LangServe（服务面）：把 Agent Runtime 暴露为稳定 API（/invoke /stream /state），方便任何系统接入。

LangGraph（内核）：把复杂任务表达成图（节点/边/分支/循环），承载“推理结构 + 状态机”。

Context / Index / Docs：上下文不是聊天记录，而是“工程事实 + 检索证据 + 变更范围”。Index 用于代码与文档的结构化入口。

Memories：长期知识（坑位、红线、决策、模块约束），存到可检索的 KB / 向量库 / SQL。

Rules：组织级硬约束（合规、风险、变更权限、操作白名单）。

Command / Skills：把高风险动作拆成“批准过的最小动作单元”，Agent 只能通过 Skills 执行关键操作。

Tools / MCP：Tools 是能力；MCP 是把能力标准化接入模型的协议层/适配层（让 Tool 不再散落在脚本里）。

Tracing：必须有。否则你只是在“放大随机性”。