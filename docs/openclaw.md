# OpenClaw 项目语义架构

## 本质定位

OpenClaw 是一个**本地优先的个人 AI 助手控制平面框架**，而非云端 AI 服务或多租户平台。 [1](#0-0) 

核心是单一长生命周期 Gateway WebSocket 服务器，统一管理多个消息通道（WhatsApp/Telegram/Slack/Discord 等）、AI 代理会话、工具执行和设备节点。 [2](#0-1) 

不是什么：不是 LLM 推理引擎本身，不是消息中间件，不是通用 RPC 框架。

## 架构分层

### 控制平面层（稳定抽象）
Gateway WebSocket 协议是系统核心抽象边界。 [3](#0-2) 

三种帧类型构成协议基础：
- Request (`type: "req"`) - 客户端到 Gateway 的 RPC 调用
- Response (`type: "res"`) - Gateway 的应答
- Event (`type: "event"`) - Gateway 的服务器推送 [4](#0-3) 

协议通过 TypeBox 模式强制类型验证，版本化演进。所有方法和事件在 `server-methods-list.ts` 中注册。 [5](#0-4) 

### 路由层（核心不变式）
会话键（Session Key）编码路由上下文：`agent:<agentId>:<channel>:<scope>:<identifier>`。 [6](#0-5) 

入站路由通过 `resolveAgentRoute` 根据 bindings 配置将消息分配给特定 agent。 [7](#0-6) 

出站分发检查 `OriginatingChannel` 实现跨通道回复。 [8](#0-7) 

### Agent 运行时层（易变实现）
Pi-embedded runner 封装 LLM 调用、工具执行、流式响应。 [9](#0-8) 

工具策略通过 allow/deny 列表控制可用工具，deny 优先级高于 allow。 [10](#0-9) 

Sandbox 配置控制执行边界：`mode` (off/non-main/all)、`scope` (session/agent/shared)、`workspaceAccess` (none/ro/rw)。 [11](#0-10) 

### Channel 插件层（可扩展边界）
所有消息通道作为插件注册，通过统一 `ChannelPlugin` 接口对接。 [12](#0-11) 

DM 安全策略三级：pairing（默认）、allowlist、open。未配对发送者会收到 8 字符配对码。 [13](#0-12) 

### 会话持久化层（稳定存储契约）
双层存储模型：
- `sessions.json` 保存会话元数据
- `*.jsonl` 追加式保存消息历史 [14](#0-13) 

会话历史可按类型限制（DM vs 群组），compaction 自动压缩旧消息。 [15](#0-14) 

## 关键模块职责

### `src/gateway/`
Gateway 启动、WebSocket 运行时、方法分发、事件广播。 [16](#0-15) 

修改此层属高风险：影响所有客户端协议兼容性。

### `src/agents/`
Agent 运行时、工具定义、sandbox 策略、skills 加载、模型切换。 [17](#0-16) 

扩展工具应注册到 plugin registry，不应直接修改 pi-tools.ts。

### `src/routing/`
会话键构造、bindings 匹配、agent 路由决策。 [18](#0-17) 

路由逻辑修改需同步更新会话键解析。

### `src/channels/`
通道配置规范化、allowlist 匹配、typing/presence 抽象。 [19](#0-18) 

通道特定实现应作为插件在 `extensions/` 或 `src/channels/plugins/` 中。

### `src/plugins/`
插件发现、加载、注册、生命周期钩子运行。 [20](#0-19) 

所有扩展点通过 `OpenClawPluginApi` 暴露。 [21](#0-20) 

### `src/config/`
配置加载、验证、热重载、运行时覆盖。 [22](#0-21) 

配置模式由多个 `types.*.ts` 模块组成，修改需更新 Zod schema。 [23](#0-22) 

## 系统生命周期

### 启动阶段
1. 入口点规范化 argv、应用 profile env [24](#0-23) 
2. 加载配置文件 `~/.openclaw/openclaw.json` [25](#0-24) 
3. 插件发现：bundled → global → workspace → config paths [26](#0-25) 
4. 插件加载：manifest 验证 → 模块加载 → register() 调用 [20](#0-19) 
5. Gateway 绑定地址解析、TLS/auth 配置应用 [27](#0-26) 
6. 启动 WebSocket 服务器、HTTP endpoints、Canvas Host [28](#0-27) 
7. Channel monitors 连接（WhatsApp/Telegram/Slack 等） [29](#0-28) 
8. Cron 调度器、维护定时器启动 [30](#0-29) 
9. 配置热重载监听器、discovery runtime 启动 [31](#0-30) 

### 运行时循环
1. 客户端 WebSocket 握手（connect 请求验证）
2. 消息入站：Channel → `resolveAgentRoute` → 会话键构造
3. Agent 调用：加载历史 → 工具注册 → Pi runner 执行 → 流式响应
4. 工具执行：策略检查 → sandbox/host/node 路由 → 结果持久化
5. 消息出站：`routeReply` 决策 → 通道分发 → ack 反应
6. 事件广播：presence/tick/agent/health 推送到所有客户端

### 关闭阶段
Gateway 关闭处理器协调所有子系统优雅停机。 [32](#0-31) 

## 扩展点分类

### 显式插件接口
**工具注册**：`api.registerTool(definition, handler)`
新工具应实现为插件，注册到 registry，不应修改核心 pi-tools.ts。 [33](#0-32) 

**通道集成**：`api.registerChannel(plugin)`
新消息平台作为 ChannelPlugin，实现 onboarding/monitor/outbound/actions。 [34](#0-33) 

**生命周期钩子**：14 个钩子点涵盖 agent/tool/message/gateway 事件
钩子优先于直接修改核心逻辑。 [21](#0-20) 

**模型提供商**：`api.registerProvider(id, authHandler)`
新 LLM 提供商通过 provider 插件集成。 [35](#0-34) 

**HTTP 端点**：`api.registerHttpRoute(path, handler)`
新 API 端点注册到 Gateway HTTP 服务器。 [36](#0-35) 

**Gateway RPC 方法**：`api.registerGatewayMethod(name, handler)`
新控制平面方法扩展协议。 [37](#0-36) 

### Skills 系统（隐式扩展）
三层优先级：workspace > managed > bundled
新技能放入 `~/.openclaw/workspace/skills/<name>/SKILL.md`。 [38](#0-37) 

Skills 通过 YAML frontmatter 定义工具规范，自动注入系统提示。

### 配置驱动扩展
**Bindings 路由**：无需代码修改即可配置 channel→agent 映射
修改 `routing.bindings` 影响消息路由决策。 [39](#0-38) 

**Sandbox 策略**：按 agent 配置隔离级别
per-agent sandbox 配置覆盖全局默认。 [40](#0-39) 

**工具过滤**：allow/deny 列表无需重编译
修改 `tools.sandbox.tools.allow` 动态控制工具可用性。 [41](#0-40) 

## 不变式约束

### 协议契约
- 首帧必须是 `connect` 请求，否则连接关闭 [42](#0-41) 
- Request 帧必须携带唯一 `id`，Response 必须匹配
- Event 帧包含可选 `seq` 和 `stateVersion` 用于状态同步
- 协议版本不匹配拒绝握手

### 会话隔离
- 会话键唯一标识路由上下文，不可跨会话混淆消息
- 非 main 会话默认不共享敏感工具（可通过 sandbox 配置放开）
- 会话历史按会话键分文件存储，compaction 不跨会话

### 安全边界
- DM 默认 `dmPolicy="pairing"`，未配对发送者消息被拦截 [43](#0-42) 
- 配对码 1 小时过期，每通道最多 3 个待批准请求
- Sandbox 工具执行不能逃逸 Docker 容器（除非显式 elevated 授权）
- Bind mounts 穿透 sandbox 文件系统，属安全敏感配置

### 配置热重载限制
- 关键配置路径（gateway.bind、gateway.port、channels 凭据）触发重启
- 热重载仅应用"安全"路径（cron、browser、部分 channel 配置） [31](#0-30) 
- 重载模式：off/restart/hot/hybrid（默认 hybrid）

### Gateway 单例假设
- 每主机仅运行一个 Gateway 实例（通过 gateway.lock 文件保证） [44](#0-43) 
- 所有通道连接（WhatsApp session）由 Gateway 独占
- 多 Gateway 架构需手动通道隔离（不同 accounts）

## 高风险修改类型

### 协议层变更
修改 `src/gateway/protocol/schema/*.ts` 影响所有客户端（macOS app、CLI、UI）。
必须维护向后兼容或升级协议版本号。 [3](#0-2) 

### 会话键格式变更
`buildAgentPeerSessionKey` 逻辑变更导致历史会话无法加载。
需迁移脚本重命名会话文件。 [6](#0-5) 

### 核心路由逻辑
`resolveAgentRoute` 修改影响所有入站消息分发。
需全通道回归测试。 [7](#0-6) 

### Sandbox 创建参数
`buildSandboxCreateArgs` 安全标志变更影响隔离强度。
移除 hardening flags 削弱安全性。 [45](#0-44) 

### 配置模式破坏性变更
Zod schema 字段重命名/移除破坏现有配置文件。
需提供迁移路径或保持字段别名。 [46](#0-45) 

## 并发模型约束

### Gateway 单线程事件循环
Gateway 主循环运行在 Node.js 单线程，长操作必须异步化。
工具执行通过子进程/Docker 隔离避免阻塞。 [16](#0-15) 

### Agent 运行并发控制
Lane 系统限制同会话并发执行，避免消息乱序。 [47](#0-46) 

Per-agent 可配置 `agents.defaults.queue.concurrent` 控制全局并发度。 [48](#0-47) 

### 工具执行隔离
Sandbox 工具在独立 Docker 容器执行，异步等待结果。
Host 工具在 Gateway 进程执行，需避免阻塞操作。
Node 工具通过 WebSocket RPC 调用设备，网络延迟敏感。 [49](#0-48) 

## Notes

本文档面向修改 OpenClaw 代码库的 AI 助手。关键理解：

1. **Gateway 是中心**：所有状态流经 WebSocket 控制平面，不要绕过它构建点对点通道
2. **插件优先**：优先通过插件扩展而非修改核心模块
3. **会话键不可变**：路由编码在会话键中，修改格式需迁移历史数据
4. **安全默认严格**：DM pairing、sandbox 隔离、工具策略层层防御，放宽需明确意图
5. **配置热重载有限**：关键路径变更必须重启，测试时注意 reload mode

扩展新功能时：
- 新消息平台 → Channel Plugin
- 新 AI 能力 → Tool Plugin 或 Skill
- 新控制命令 → Gateway RPC Method Plugin
- 新数据源 → HTTP Handler Plugin + Tool

避免直接修改 `src/gateway/server.impl.ts`、`src/routing/resolve-route.ts`、`src/agents/pi-embedded-runner/run.ts` 等核心流程文件，除非明确理解全局影响。

### Citations

**File:** README.md (L18-22)
```markdown
**OpenClaw** is a *personal AI assistant* you run on your own devices.
It answers you on the channels you already use (WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, Microsoft Teams, WebChat), plus extension channels like BlueBubbles, Matrix, Zalo, and Zalo Personal. It can speak and listen on macOS/iOS/Android, and can render a live Canvas you control. The Gateway is just the control plane — the product is the assistant.

If you want a personal, single-user assistant that feels local, fast, and always-on, this is it.

```

**File:** docs/concepts/architecture.md (L12-20)
```markdown
- A single long‑lived **Gateway** owns all messaging surfaces (WhatsApp via
  Baileys, Telegram via grammY, Slack, Discord, Signal, iMessage, WebChat).
- Control-plane clients (macOS app, CLI, web UI, automations) connect to the
  Gateway over **WebSocket** on the configured bind host (default
  `127.0.0.1:18789`).
- **Nodes** (macOS/iOS/Android/headless) also connect over **WebSocket**, but
  declare `role: node` with explicit caps/commands.
- One Gateway per host; it is the only place that opens a WhatsApp session.
- A **canvas host** (default `18793`) serves agent‑editable HTML and A2UI.
```

**File:** docs/concepts/architecture.md (L68-79)
```markdown
## Wire protocol (summary)

- Transport: WebSocket, text frames with JSON payloads.
- First frame **must** be `connect`.
- After handshake:
  - Requests: `{type:"req", id, method, params}` → `{type:"res", id, ok, payload|error}`
  - Events: `{type:"event", event, payload, seq?, stateVersion?}`
- If `OPENCLAW_GATEWAY_TOKEN` (or `--token`) is set, `connect.params.auth.token`
  must match or the socket closes.
- Idempotency keys are required for side‑effecting methods (`send`, `agent`) to
  safely retry; the server keeps a short‑lived dedupe cache.
- Nodes must include `role: "node"` plus caps/commands/permissions in `connect`.
```

**File:** src/gateway/protocol/schema.ts (L1-16)
```typescript
export * from "./schema/agent.js";
export * from "./schema/agents-models-skills.js";
export * from "./schema/channels.js";
export * from "./schema/config.js";
export * from "./schema/cron.js";
export * from "./schema/error-codes.js";
export * from "./schema/exec-approvals.js";
export * from "./schema/devices.js";
export * from "./schema/frames.js";
export * from "./schema/logs-chat.js";
export * from "./schema/nodes.js";
export * from "./schema/protocol-schemas.js";
export * from "./schema/sessions.js";
export * from "./schema/snapshot.js";
export * from "./schema/types.js";
export * from "./schema/wizard.js";
```

**File:** src/gateway/server-methods-list.ts (L1-100)
```typescript
import { listChannelPlugins } from "../channels/plugins/index.js";

const BASE_METHODS = [
  "health",
  "logs.tail",
  "channels.status",
  "channels.logout",
  "status",
  "usage.status",
  "usage.cost",
  "tts.status",
  "tts.providers",
  "tts.enable",
  "tts.disable",
  "tts.convert",
  "tts.setProvider",
  "config.get",
  "config.set",
  "config.apply",
  "config.patch",
  "config.schema",
  "exec.approvals.get",
  "exec.approvals.set",
  "exec.approvals.node.get",
  "exec.approvals.node.set",
  "exec.approval.request",
  "exec.approval.resolve",
  "wizard.start",
  "wizard.next",
  "wizard.cancel",
  "wizard.status",
  "talk.mode",
  "models.list",
  "agents.list",
  "skills.status",
  "skills.bins",
  "skills.install",
  "skills.update",
  "update.run",
  "voicewake.get",
  "voicewake.set",
  "sessions.list",
  "sessions.preview",
  "sessions.patch",
  "sessions.reset",
  "sessions.delete",
  "sessions.compact",
  "last-heartbeat",
  "set-heartbeats",
  "wake",
  "node.pair.request",
  "node.pair.list",
  "node.pair.approve",
  "node.pair.reject",
  "node.pair.verify",
  "device.pair.list",
  "device.pair.approve",
  "device.pair.reject",
  "device.token.rotate",
  "device.token.revoke",
  "node.rename",
  "node.list",
  "node.describe",
  "node.invoke",
  "node.invoke.result",
  "node.event",
  "cron.list",
  "cron.status",
  "cron.add",
  "cron.update",
  "cron.remove",
  "cron.run",
  "cron.runs",
  "system-presence",
  "system-event",
  "send",
  "agent",
  "agent.identity.get",
  "agent.wait",
  "browser.request",
  // WebChat WebSocket-native chat methods
  "chat.history",
  "chat.abort",
  "chat.send",
];

export function listGatewayMethods(): string[] {
  const channelMethods = listChannelPlugins().flatMap((plugin) => plugin.gatewayMethods ?? []);
  return Array.from(new Set([...BASE_METHODS, ...channelMethods]));
}

export const GATEWAY_EVENTS = [
  "connect.challenge",
  "agent",
  "chat",
  "presence",
  "tick",
  "talk.mode",
  "shutdown",
  "health",
```

**File:** src/routing/session-key.ts (L1-100)
```typescript
import { parseAgentSessionKey, type ParsedAgentSessionKey } from "../sessions/session-key-utils.js";

export {
  isAcpSessionKey,
  isSubagentSessionKey,
  parseAgentSessionKey,
  type ParsedAgentSessionKey,
} from "../sessions/session-key-utils.js";

export const DEFAULT_AGENT_ID = "main";
export const DEFAULT_MAIN_KEY = "main";
export const DEFAULT_ACCOUNT_ID = "default";

// Pre-compiled regex
const VALID_ID_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/i;
const INVALID_CHARS_RE = /[^a-z0-9_-]+/g;
const LEADING_DASH_RE = /^-+/;
const TRAILING_DASH_RE = /-+$/;

function normalizeToken(value: string | undefined | null): string {
  return (value ?? "").trim().toLowerCase();
}

export function normalizeMainKey(value: string | undefined | null): string {
  const trimmed = (value ?? "").trim();
  return trimmed ? trimmed.toLowerCase() : DEFAULT_MAIN_KEY;
}

export function toAgentRequestSessionKey(storeKey: string | undefined | null): string | undefined {
  const raw = (storeKey ?? "").trim();
  if (!raw) return undefined;
  return parseAgentSessionKey(raw)?.rest ?? raw;
}

export function toAgentStoreSessionKey(params: {
  agentId: string;
  requestKey: string | undefined | null;
  mainKey?: string | undefined;
}): string {
  const raw = (params.requestKey ?? "").trim();
  if (!raw || raw === DEFAULT_MAIN_KEY) {
    return buildAgentMainSessionKey({ agentId: params.agentId, mainKey: params.mainKey });
  }
  const lowered = raw.toLowerCase();
  if (lowered.startsWith("agent:")) return lowered;
  if (lowered.startsWith("subagent:")) {
    return `agent:${normalizeAgentId(params.agentId)}:${lowered}`;
  }
  return `agent:${normalizeAgentId(params.agentId)}:${lowered}`;
}

export function resolveAgentIdFromSessionKey(sessionKey: string | undefined | null): string {
  const parsed = parseAgentSessionKey(sessionKey);
  return normalizeAgentId(parsed?.agentId ?? DEFAULT_AGENT_ID);
}

export function normalizeAgentId(value: string | undefined | null): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return DEFAULT_AGENT_ID;
  // Keep it path-safe + shell-friendly.
  if (VALID_ID_RE.test(trimmed)) return trimmed.toLowerCase();
  // Best-effort fallback: collapse invalid characters to "-"
  return (
    trimmed
      .toLowerCase()
      .replace(INVALID_CHARS_RE, "-")
      .replace(LEADING_DASH_RE, "")
      .replace(TRAILING_DASH_RE, "")
      .slice(0, 64) || DEFAULT_AGENT_ID
  );
}

export function sanitizeAgentId(value: string | undefined | null): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return DEFAULT_AGENT_ID;
  if (VALID_ID_RE.test(trimmed)) return trimmed.toLowerCase();
  return (
    trimmed
      .toLowerCase()
      .replace(INVALID_CHARS_RE, "-")
      .replace(LEADING_DASH_RE, "")
      .replace(TRAILING_DASH_RE, "")
      .slice(0, 64) || DEFAULT_AGENT_ID
  );
}

export function normalizeAccountId(value: string | undefined | null): string {
  const trimmed = (value ?? "").trim();
  if (!trimmed) return DEFAULT_ACCOUNT_ID;
  if (VALID_ID_RE.test(trimmed)) return trimmed.toLowerCase();
  return (
    trimmed
      .toLowerCase()
      .replace(INVALID_CHARS_RE, "-")
      .replace(LEADING_DASH_RE, "")
      .replace(TRAILING_DASH_RE, "")
      .slice(0, 64) || DEFAULT_ACCOUNT_ID
  );
}

```

**File:** src/routing/resolve-route.ts (L20-45)
```typescript
export type ResolveAgentRouteInput = {
  cfg: OpenClawConfig;
  channel: string;
  accountId?: string | null;
  peer?: RoutePeer | null;
  guildId?: string | null;
  teamId?: string | null;
};

export type ResolvedAgentRoute = {
  agentId: string;
  channel: string;
  accountId: string;
  /** Internal session key used for persistence + concurrency. */
  sessionKey: string;
  /** Convenience alias for direct-chat collapse. */
  mainSessionKey: string;
  /** Match description for debugging/logging. */
  matchedBy:
    | "binding.peer"
    | "binding.guild"
    | "binding.team"
    | "binding.account"
    | "binding.channel"
    | "default";
};
```

**File:** src/routing/resolve-route.ts (L69-90)
```typescript
export function buildAgentSessionKey(params: {
  agentId: string;
  channel: string;
  accountId?: string | null;
  peer?: RoutePeer | null;
  /** DM session scope. */
  dmScope?: "main" | "per-peer" | "per-channel-peer" | "per-account-channel-peer";
  identityLinks?: Record<string, string[]>;
}): string {
  const channel = normalizeToken(params.channel) || "unknown";
  const peer = params.peer;
  return buildAgentPeerSessionKey({
    agentId: params.agentId,
    mainKey: DEFAULT_MAIN_KEY,
    channel,
    accountId: params.accountId,
    peerKind: peer?.kind ?? "dm",
    peerId: peer ? normalizeId(peer.id) || "unknown" : null,
    dmScope: params.dmScope,
    identityLinks: params.identityLinks,
  });
}
```

**File:** src/auto-reply/reply/route-reply.ts (L1-100)
```typescript
/**
 * Provider-agnostic reply router.
 *
 * Routes replies to the originating channel based on OriginatingChannel/OriginatingTo
 * instead of using the session's lastChannel. This ensures replies go back to the
 * provider where the message originated, even when the main session is shared
 * across multiple providers.
 */

import { resolveSessionAgentId } from "../../agents/agent-scope.js";
import { resolveEffectiveMessagesConfig } from "../../agents/identity.js";
import { normalizeChannelId } from "../../channels/plugins/index.js";
import type { OpenClawConfig } from "../../config/config.js";
import { INTERNAL_MESSAGE_CHANNEL } from "../../utils/message-channel.js";
import type { OriginatingChannelType } from "../templating.js";
import type { ReplyPayload } from "../types.js";
import { normalizeReplyPayload } from "./normalize-reply.js";

export type RouteReplyParams = {
  /** The reply payload to send. */
  payload: ReplyPayload;
  /** The originating channel type (telegram, slack, etc). */
  channel: OriginatingChannelType;
  /** The destination chat/channel/user ID. */
  to: string;
  /** Session key for deriving agent identity defaults (multi-agent). */
  sessionKey?: string;
  /** Provider account id (multi-account). */
  accountId?: string;
  /** Thread id for replies (Telegram topic id or Matrix thread event id). */
  threadId?: string | number;
  /** Config for provider-specific settings. */
  cfg: OpenClawConfig;
  /** Optional abort signal for cooperative cancellation. */
  abortSignal?: AbortSignal;
  /** Mirror reply into session transcript (default: true when sessionKey is set). */
  mirror?: boolean;
};

export type RouteReplyResult = {
  /** Whether the reply was sent successfully. */
  ok: boolean;
  /** Optional message ID from the provider. */
  messageId?: string;
  /** Error message if the send failed. */
  error?: string;
};

/**
 * Routes a reply payload to the specified channel.
 *
 * This function provides a unified interface for sending messages to any
 * supported provider. It's used by the followup queue to route replies
 * back to the originating channel when OriginatingChannel/OriginatingTo
 * are set.
 */
export async function routeReply(params: RouteReplyParams): Promise<RouteReplyResult> {
  const { payload, channel, to, accountId, threadId, cfg, abortSignal } = params;

  // Debug: `pnpm test src/auto-reply/reply/route-reply.test.ts`
  const responsePrefix = params.sessionKey
    ? resolveEffectiveMessagesConfig(
        cfg,
        resolveSessionAgentId({
          sessionKey: params.sessionKey,
          config: cfg,
        }),
      ).responsePrefix
    : cfg.messages?.responsePrefix === "auto"
      ? undefined
      : cfg.messages?.responsePrefix;
  const normalized = normalizeReplyPayload(payload, {
    responsePrefix,
  });
  if (!normalized) return { ok: true };

  let text = normalized.text ?? "";
  let mediaUrls = (normalized.mediaUrls?.filter(Boolean) ?? []).length
    ? (normalized.mediaUrls?.filter(Boolean) as string[])
    : normalized.mediaUrl
      ? [normalized.mediaUrl]
      : [];
  const replyToId = normalized.replyToId;

  // Skip empty replies.
  if (!text.trim() && mediaUrls.length === 0) {
    return { ok: true };
  }

  if (channel === INTERNAL_MESSAGE_CHANNEL) {
    return {
      ok: false,
      error: "Webchat routing not supported for queued replies",
    };
  }

  const channelId = normalizeChannelId(channel) ?? null;
  if (!channelId) {
    return { ok: false, error: `Unknown channel: ${String(channel)}` };
  }
```

**File:** src/agents/pi-embedded-runner.ts (L1-27)
```typescript
export type { MessagingToolSend } from "./pi-embedded-messaging.js";
export { compactEmbeddedPiSession } from "./pi-embedded-runner/compact.js";
export { applyExtraParamsToAgent, resolveExtraParams } from "./pi-embedded-runner/extra-params.js";

export { applyGoogleTurnOrderingFix } from "./pi-embedded-runner/google.js";
export {
  getDmHistoryLimitFromSessionKey,
  limitHistoryTurns,
} from "./pi-embedded-runner/history.js";
export { resolveEmbeddedSessionLane } from "./pi-embedded-runner/lanes.js";
export { runEmbeddedPiAgent } from "./pi-embedded-runner/run.js";
export {
  abortEmbeddedPiRun,
  isEmbeddedPiRunActive,
  isEmbeddedPiRunStreaming,
  queueEmbeddedPiMessage,
  waitForEmbeddedPiRunEnd,
} from "./pi-embedded-runner/runs.js";
export { buildEmbeddedSandboxInfo } from "./pi-embedded-runner/sandbox-info.js";
export { createSystemPromptOverride } from "./pi-embedded-runner/system-prompt.js";
export { splitSdkTools } from "./pi-embedded-runner/tool-split.js";
export type {
  EmbeddedPiAgentMeta,
  EmbeddedPiCompactResult,
  EmbeddedPiRunMeta,
  EmbeddedPiRunResult,
} from "./pi-embedded-runner/types.js";
```

**File:** src/agents/pi-tools.policy.ts (L1-100)
```typescript
import type { OpenClawConfig } from "../config/config.js";
import { getChannelDock } from "../channels/dock.js";
import { resolveChannelGroupToolsPolicy } from "../config/group-policy.js";
import { resolveAgentConfig, resolveAgentIdFromSessionKey } from "./agent-scope.js";
import type { AnyAgentTool } from "./pi-tools.types.js";
import type { SandboxToolPolicy } from "./sandbox.js";
import { expandToolGroups, normalizeToolName } from "./tool-policy.js";
import { normalizeMessageChannel } from "../utils/message-channel.js";
import { resolveThreadParentSessionKey } from "../sessions/session-key-utils.js";

type CompiledPattern =
  | { kind: "all" }
  | { kind: "exact"; value: string }
  | { kind: "regex"; value: RegExp };

function compilePattern(pattern: string): CompiledPattern {
  const normalized = normalizeToolName(pattern);
  if (!normalized) return { kind: "exact", value: "" };
  if (normalized === "*") return { kind: "all" };
  if (!normalized.includes("*")) return { kind: "exact", value: normalized };
  const escaped = normalized.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return {
    kind: "regex",
    value: new RegExp(`^${escaped.replaceAll("\\*", ".*")}$`),
  };
}

function compilePatterns(patterns?: string[]): CompiledPattern[] {
  if (!Array.isArray(patterns)) return [];
  return expandToolGroups(patterns)
    .map(compilePattern)
    .filter((pattern) => pattern.kind !== "exact" || pattern.value);
}

function matchesAny(name: string, patterns: CompiledPattern[]): boolean {
  for (const pattern of patterns) {
    if (pattern.kind === "all") return true;
    if (pattern.kind === "exact" && name === pattern.value) return true;
    if (pattern.kind === "regex" && pattern.value.test(name)) return true;
  }
  return false;
}

function makeToolPolicyMatcher(policy: SandboxToolPolicy) {
  const deny = compilePatterns(policy.deny);
  const allow = compilePatterns(policy.allow);
  return (name: string) => {
    const normalized = normalizeToolName(name);
    if (matchesAny(normalized, deny)) return false;
    if (allow.length === 0) return true;
    if (matchesAny(normalized, allow)) return true;
    if (normalized === "apply_patch" && matchesAny("exec", allow)) return true;
    return false;
  };
}

const DEFAULT_SUBAGENT_TOOL_DENY = [
  // Session management - main agent orchestrates
  "sessions_list",
  "sessions_history",
  "sessions_send",
  "sessions_spawn",
  // System admin - dangerous from subagent
  "gateway",
  "agents_list",
  // Interactive setup - not a task
  "whatsapp_login",
  // Status/scheduling - main agent coordinates
  "session_status",
  "cron",
  // Memory - pass relevant info in spawn prompt instead
  "memory_search",
  "memory_get",
];

export function resolveSubagentToolPolicy(cfg?: OpenClawConfig): SandboxToolPolicy {
  const configured = cfg?.tools?.subagents?.tools;
  const deny = [
    ...DEFAULT_SUBAGENT_TOOL_DENY,
    ...(Array.isArray(configured?.deny) ? configured.deny : []),
  ];
  const allow = Array.isArray(configured?.allow) ? configured.allow : undefined;
  return { allow, deny };
}

export function isToolAllowedByPolicyName(name: string, policy?: SandboxToolPolicy): boolean {
  if (!policy) return true;
  return makeToolPolicyMatcher(policy)(name);
}

export function filterToolsByPolicy(tools: AnyAgentTool[], policy?: SandboxToolPolicy) {
  if (!policy) return tools;
  const matcher = makeToolPolicyMatcher(policy);
  return tools.filter((tool) => matcher(tool.name));
}

type ToolPolicyConfig = {
  allow?: string[];
  alsoAllow?: string[];
  deny?: string[];
```

**File:** src/agents/sandbox.ts (L1-100)
```typescript
export {
  resolveSandboxBrowserConfig,
  resolveSandboxConfigForAgent,
  resolveSandboxDockerConfig,
  resolveSandboxPruneConfig,
  resolveSandboxScope,
} from "./sandbox/config.js";
export {
  DEFAULT_SANDBOX_BROWSER_IMAGE,
  DEFAULT_SANDBOX_COMMON_IMAGE,
  DEFAULT_SANDBOX_IMAGE,
} from "./sandbox/constants.js";
export { ensureSandboxWorkspaceForSession, resolveSandboxContext } from "./sandbox/context.js";

export { buildSandboxCreateArgs } from "./sandbox/docker.js";
export {
  listSandboxBrowsers,
  listSandboxContainers,
  removeSandboxBrowserContainer,
  removeSandboxContainer,
  type SandboxBrowserInfo,
  type SandboxContainerInfo,
} from "./sandbox/manage.js";
export {
  formatSandboxToolPolicyBlockedMessage,
  resolveSandboxRuntimeStatus,
} from "./sandbox/runtime-status.js";

export { resolveSandboxToolPolicyForAgent } from "./sandbox/tool-policy.js";

export type {
  SandboxBrowserConfig,
  SandboxBrowserContext,
  SandboxConfig,
  SandboxContext,
  SandboxDockerConfig,
  SandboxPruneConfig,
  SandboxScope,
  SandboxToolPolicy,
  SandboxToolPolicyResolved,
  SandboxToolPolicySource,
  SandboxWorkspaceAccess,
  SandboxWorkspaceInfo,
} from "./sandbox/types.js";


```

**File:** src/channels/plugins/index.ts (L29-51)
```typescript
export function listChannelPlugins(): ChannelPlugin[] {
  const combined = dedupeChannels(listPluginChannels());
  return combined.sort((a, b) => {
    const indexA = CHAT_CHANNEL_ORDER.indexOf(a.id as ChatChannelId);
    const indexB = CHAT_CHANNEL_ORDER.indexOf(b.id as ChatChannelId);
    const orderA = a.meta.order ?? (indexA === -1 ? 999 : indexA);
    const orderB = b.meta.order ?? (indexB === -1 ? 999 : indexB);
    if (orderA !== orderB) return orderA - orderB;
    return a.id.localeCompare(b.id);
  });
}

export function getChannelPlugin(id: ChannelId): ChannelPlugin | undefined {
  const resolvedId = String(id).trim();
  if (!resolvedId) return undefined;
  return listChannelPlugins().find((plugin) => plugin.id === resolvedId);
}

export function normalizeChannelId(raw?: string | null): ChannelId | null {
  // Channel docking: keep input normalization centralized in src/channels/registry.ts.
  // Plugin registry must be initialized before calling.
  return normalizeAnyChannelId(raw);
}
```

**File:** src/pairing/pairing-store.ts (L1-100)
```typescript
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import lockfile from "proper-lockfile";
import { getPairingAdapter } from "../channels/plugins/pairing.js";
import type { ChannelId, ChannelPairingAdapter } from "../channels/plugins/types.js";
import { resolveOAuthDir, resolveStateDir } from "../config/paths.js";

const PAIRING_CODE_LENGTH = 8;
const PAIRING_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const PAIRING_PENDING_TTL_MS = 60 * 60 * 1000;
const PAIRING_PENDING_MAX = 3;
const PAIRING_STORE_LOCK_OPTIONS = {
  retries: {
    retries: 10,
    factor: 2,
    minTimeout: 100,
    maxTimeout: 10_000,
    randomize: true,
  },
  stale: 30_000,
} as const;

export type PairingChannel = ChannelId;

export type PairingRequest = {
  id: string;
  code: string;
  createdAt: string;
  lastSeenAt: string;
  meta?: Record<string, string>;
};

type PairingStore = {
  version: 1;
  requests: PairingRequest[];
};

type AllowFromStore = {
  version: 1;
  allowFrom: string[];
};

function resolveCredentialsDir(env: NodeJS.ProcessEnv = process.env): string {
  const stateDir = resolveStateDir(env, os.homedir);
  return resolveOAuthDir(env, stateDir);
}

/** Sanitize channel ID for use in filenames (prevent path traversal). */
function safeChannelKey(channel: PairingChannel): string {
  const raw = String(channel).trim().toLowerCase();
  if (!raw) throw new Error("invalid pairing channel");
  const safe = raw.replace(/[\\/:*?"<>|]/g, "_").replace(/\.\./g, "_");
  if (!safe || safe === "_") throw new Error("invalid pairing channel");
  return safe;
}

function resolvePairingPath(channel: PairingChannel, env: NodeJS.ProcessEnv = process.env): string {
  return path.join(resolveCredentialsDir(env), `${safeChannelKey(channel)}-pairing.json`);
}

function resolveAllowFromPath(
  channel: PairingChannel,
  env: NodeJS.ProcessEnv = process.env,
): string {
  return path.join(resolveCredentialsDir(env), `${safeChannelKey(channel)}-allowFrom.json`);
}

function safeParseJson<T>(raw: string): T | null {
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

async function readJsonFile<T>(
  filePath: string,
  fallback: T,
): Promise<{ value: T; exists: boolean }> {
  try {
    const raw = await fs.promises.readFile(filePath, "utf-8");
    const parsed = safeParseJson<T>(raw);
    if (parsed == null) return { value: fallback, exists: true };
    return { value: parsed, exists: true };
  } catch (err) {
    const code = (err as { code?: string }).code;
    if (code === "ENOENT") return { value: fallback, exists: false };
    return { value: fallback, exists: false };
  }
}

async function writeJsonFile(filePath: string, value: unknown): Promise<void> {
  const dir = path.dirname(filePath);
  await fs.promises.mkdir(dir, { recursive: true, mode: 0o700 });
  const tmp = path.join(dir, `${path.basename(filePath)}.${crypto.randomUUID()}.tmp`);
  await fs.promises.writeFile(tmp, `${JSON.stringify(value, null, 2)}\n`, {
    encoding: "utf-8",
```

**File:** src/config/sessions/types.ts (L1-100)
```typescript
import crypto from "node:crypto";

import type { Skill } from "@mariozechner/pi-coding-agent";
import type { NormalizedChatType } from "../../channels/chat-type.js";
import type { ChannelId } from "../../channels/plugins/types.js";
import type { DeliveryContext } from "../../utils/delivery-context.js";
import type { TtsAutoMode } from "../types.tts.js";

export type SessionScope = "per-sender" | "global";

export type SessionChannelId = ChannelId | "webchat";

export type SessionChatType = NormalizedChatType;

export type SessionOrigin = {
  label?: string;
  provider?: string;
  surface?: string;
  chatType?: SessionChatType;
  from?: string;
  to?: string;
  accountId?: string;
  threadId?: string | number;
};

export type SessionEntry = {
  /**
   * Last delivered heartbeat payload (used to suppress duplicate heartbeat notifications).
   * Stored on the main session entry.
   */
  lastHeartbeatText?: string;
  /** Timestamp (ms) when lastHeartbeatText was delivered. */
  lastHeartbeatSentAt?: number;
  sessionId: string;
  updatedAt: number;
  sessionFile?: string;
  /** Parent session key that spawned this session (used for sandbox session-tool scoping). */
  spawnedBy?: string;
  systemSent?: boolean;
  abortedLastRun?: boolean;
  chatType?: SessionChatType;
  thinkingLevel?: string;
  verboseLevel?: string;
  reasoningLevel?: string;
  elevatedLevel?: string;
  ttsAuto?: TtsAutoMode;
  execHost?: string;
  execSecurity?: string;
  execAsk?: string;
  execNode?: string;
  responseUsage?: "on" | "off" | "tokens" | "full";
  providerOverride?: string;
  modelOverride?: string;
  authProfileOverride?: string;
  authProfileOverrideSource?: "auto" | "user";
  authProfileOverrideCompactionCount?: number;
  groupActivation?: "mention" | "always";
  groupActivationNeedsSystemIntro?: boolean;
  sendPolicy?: "allow" | "deny";
  queueMode?:
    | "steer"
    | "followup"
    | "collect"
    | "steer-backlog"
    | "steer+backlog"
    | "queue"
    | "interrupt";
  queueDebounceMs?: number;
  queueCap?: number;
  queueDrop?: "old" | "new" | "summarize";
  inputTokens?: number;
  outputTokens?: number;
  totalTokens?: number;
  modelProvider?: string;
  model?: string;
  contextTokens?: number;
  compactionCount?: number;
  memoryFlushAt?: number;
  memoryFlushCompactionCount?: number;
  cliSessionIds?: Record<string, string>;
  claudeCliSessionId?: string;
  label?: string;
  displayName?: string;
  channel?: string;
  groupId?: string;
  subject?: string;
  groupChannel?: string;
  space?: string;
  origin?: SessionOrigin;
  deliveryContext?: DeliveryContext;
  lastChannel?: SessionChannelId;
  lastTo?: string;
  lastAccountId?: string;
  lastThreadId?: string | number;
  skillsSnapshot?: SessionSkillSnapshot;
  systemPromptReport?: SessionSystemPromptReport;
};

export function mergeSessionEntry(
  existing: SessionEntry | undefined,
```

**File:** src/agents/pi-embedded-runner/compact.ts (L1-100)
```typescript
import fs from "node:fs/promises";
import os from "node:os";

import {
  createAgentSession,
  estimateTokens,
  SessionManager,
  SettingsManager,
} from "@mariozechner/pi-coding-agent";

import { resolveHeartbeatPrompt } from "../../auto-reply/heartbeat.js";
import type { ReasoningLevel, ThinkLevel } from "../../auto-reply/thinking.js";
import { listChannelSupportedActions, resolveChannelMessageToolHints } from "../channel-tools.js";
import { resolveChannelCapabilities } from "../../config/channel-capabilities.js";
import type { OpenClawConfig } from "../../config/config.js";
import { getMachineDisplayName } from "../../infra/machine-name.js";
import { resolveTelegramInlineButtonsScope } from "../../telegram/inline-buttons.js";
import { resolveTelegramReactionLevel } from "../../telegram/reaction-level.js";
import { resolveSignalReactionLevel } from "../../signal/reaction-level.js";
import { type enqueueCommand, enqueueCommandInLane } from "../../process/command-queue.js";
import { normalizeMessageChannel } from "../../utils/message-channel.js";
import { isSubagentSessionKey } from "../../routing/session-key.js";
import { isReasoningTagProvider } from "../../utils/provider-utils.js";
import { resolveUserPath } from "../../utils.js";
import { resolveOpenClawAgentDir } from "../agent-paths.js";
import { resolveSessionAgentIds } from "../agent-scope.js";
import { makeBootstrapWarn, resolveBootstrapContextForRun } from "../bootstrap-files.js";
import { resolveOpenClawDocsPath } from "../docs-path.js";
import type { ExecElevatedDefaults } from "../bash-tools.js";
import { DEFAULT_MODEL, DEFAULT_PROVIDER } from "../defaults.js";
import { getApiKeyForModel, resolveModelAuthMode } from "../model-auth.js";
import { ensureOpenClawModelsJson } from "../models-config.js";
import {
  ensureSessionHeader,
  validateAnthropicTurns,
  validateGeminiTurns,
} from "../pi-embedded-helpers.js";
import {
  ensurePiCompactionReserveTokens,
  resolveCompactionReserveTokensFloor,
} from "../pi-settings.js";
import { createOpenClawCodingTools } from "../pi-tools.js";
import { resolveSandboxContext } from "../sandbox.js";
import { guardSessionManager } from "../session-tool-result-guard-wrapper.js";
import { resolveTranscriptPolicy } from "../transcript-policy.js";
import { acquireSessionWriteLock } from "../session-write-lock.js";
import {
  applySkillEnvOverrides,
  applySkillEnvOverridesFromSnapshot,
  loadWorkspaceSkillEntries,
  resolveSkillsPromptForRun,
  type SkillSnapshot,
} from "../skills.js";
import { buildEmbeddedExtensionPaths } from "./extensions.js";
import {
  logToolSchemasForGoogle,
  sanitizeSessionHistory,
  sanitizeToolsForGoogle,
} from "./google.js";
import { getDmHistoryLimitFromSessionKey, limitHistoryTurns } from "./history.js";
import { resolveGlobalLane, resolveSessionLane } from "./lanes.js";
import { log } from "./logger.js";
import { buildModelAliasLines, resolveModel } from "./model.js";
import { buildEmbeddedSandboxInfo } from "./sandbox-info.js";
import { prewarmSessionFile, trackSessionManagerAccess } from "./session-manager-cache.js";
import { buildEmbeddedSystemPrompt, createSystemPromptOverride } from "./system-prompt.js";
import { splitSdkTools } from "./tool-split.js";
import type { EmbeddedPiCompactResult } from "./types.js";
import { formatUserTime, resolveUserTimeFormat, resolveUserTimezone } from "../date-time.js";
import { describeUnknownError, mapThinkingLevel, resolveExecToolDefaults } from "./utils.js";
import { buildTtsSystemPromptHint } from "../../tts/tts.js";

export type CompactEmbeddedPiSessionParams = {
  sessionId: string;
  sessionKey?: string;
  messageChannel?: string;
  messageProvider?: string;
  agentAccountId?: string;
  authProfileId?: string;
  /** Group id for channel-level tool policy resolution. */
  groupId?: string | null;
  /** Group channel label (e.g. #general) for channel-level tool policy resolution. */
  groupChannel?: string | null;
  /** Group space label (e.g. guild/team id) for channel-level tool policy resolution. */
  groupSpace?: string | null;
  /** Parent session key for subagent policy inheritance. */
  spawnedBy?: string | null;
  sessionFile: string;
  workspaceDir: string;
  agentDir?: string;
  config?: OpenClawConfig;
  skillsSnapshot?: SkillSnapshot;
  provider?: string;
  model?: string;
  thinkLevel?: ThinkLevel;
  reasoningLevel?: ReasoningLevel;
  bashElevated?: ExecElevatedDefaults;
  customInstructions?: string;
  lane?: string;
  enqueue?: typeof enqueueCommand;
```

**File:** src/gateway/server.impl.ts (L92-150)
```typescript
export type GatewayServer = {
  close: (opts?: { reason?: string; restartExpectedMs?: number | null }) => Promise<void>;
};

export type GatewayServerOptions = {
  /**
   * Bind address policy for the Gateway WebSocket/HTTP server.
   * - loopback: 127.0.0.1
   * - lan: 0.0.0.0
   * - tailnet: bind only to the Tailscale IPv4 address (100.64.0.0/10)
   * - auto: prefer loopback, else LAN
   */
  bind?: import("../config/config.js").GatewayBindMode;
  /**
   * Advanced override for the bind host, bypassing bind resolution.
   * Prefer `bind` unless you really need a specific address.
   */
  host?: string;
  /**
   * If false, do not serve the browser Control UI.
   * Default: config `gateway.controlUi.enabled` (or true when absent).
   */
  controlUiEnabled?: boolean;
  /**
   * If false, do not serve `POST /v1/chat/completions`.
   * Default: config `gateway.http.endpoints.chatCompletions.enabled` (or false when absent).
   */
  openAiChatCompletionsEnabled?: boolean;
  /**
   * If false, do not serve `POST /v1/responses` (OpenResponses API).
   * Default: config `gateway.http.endpoints.responses.enabled` (or false when absent).
   */
  openResponsesEnabled?: boolean;
  /**
   * Override gateway auth configuration (merges with config).
   */
  auth?: import("../config/config.js").GatewayAuthConfig;
  /**
   * Override gateway Tailscale exposure configuration (merges with config).
   */
  tailscale?: import("../config/config.js").GatewayTailscaleConfig;
  /**
   * Test-only: allow canvas host startup even when NODE_ENV/VITEST would disable it.
   */
  allowCanvasHostInTests?: boolean;
  /**
   * Test-only: override the onboarding wizard runner.
   */
  wizardRunner?: (
    opts: import("../commands/onboard-types.js").OnboardOptions,
    runtime: import("../runtime.js").RuntimeEnv,
    prompter: import("../wizard/prompts.js").WizardPrompter,
  ) => Promise<void>;
};

export async function startGatewayServer(
  port = 18789,
  opts: GatewayServerOptions = {},
): Promise<GatewayServer> {
```

**File:** src/agents/pi-embedded-runner/run.ts (L1-100)
```typescript
import fs from "node:fs/promises";
import type { ThinkLevel } from "../../auto-reply/thinking.js";
import { enqueueCommandInLane } from "../../process/command-queue.js";
import { resolveUserPath } from "../../utils.js";
import { isMarkdownCapableMessageChannel } from "../../utils/message-channel.js";
import { resolveOpenClawAgentDir } from "../agent-paths.js";
import {
  isProfileInCooldown,
  markAuthProfileFailure,
  markAuthProfileGood,
  markAuthProfileUsed,
} from "../auth-profiles.js";
import {
  CONTEXT_WINDOW_HARD_MIN_TOKENS,
  CONTEXT_WINDOW_WARN_BELOW_TOKENS,
  evaluateContextWindowGuard,
  resolveContextWindowInfo,
} from "../context-window-guard.js";
import { DEFAULT_CONTEXT_TOKENS, DEFAULT_MODEL, DEFAULT_PROVIDER } from "../defaults.js";
import { FailoverError, resolveFailoverStatus } from "../failover-error.js";
import {
  ensureAuthProfileStore,
  getApiKeyForModel,
  resolveAuthProfileOrder,
  type ResolvedProviderAuth,
} from "../model-auth.js";
import { normalizeProviderId } from "../model-selection.js";
import { ensureOpenClawModelsJson } from "../models-config.js";
import {
  classifyFailoverReason,
  formatAssistantErrorText,
  isAuthAssistantError,
  isCompactionFailureError,
  isContextOverflowError,
  isFailoverAssistantError,
  isFailoverErrorMessage,
  parseImageSizeError,
  parseImageDimensionError,
  isRateLimitAssistantError,
  isTimeoutErrorMessage,
  pickFallbackThinkingLevel,
  type FailoverReason,
} from "../pi-embedded-helpers.js";
import { normalizeUsage, type UsageLike } from "../usage.js";

import { compactEmbeddedPiSessionDirect } from "./compact.js";
import { resolveGlobalLane, resolveSessionLane } from "./lanes.js";
import { log } from "./logger.js";
import { resolveModel } from "./model.js";
import { runEmbeddedAttempt } from "./run/attempt.js";
import type { RunEmbeddedPiAgentParams } from "./run/params.js";
import { buildEmbeddedRunPayloads } from "./run/payloads.js";
import type { EmbeddedPiAgentMeta, EmbeddedPiRunResult } from "./types.js";
import { describeUnknownError } from "./utils.js";

type ApiKeyInfo = ResolvedProviderAuth;

// Avoid Anthropic's refusal test token poisoning session transcripts.
const ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL = "ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL";
const ANTHROPIC_MAGIC_STRING_REPLACEMENT = "ANTHROPIC MAGIC STRING TRIGGER REFUSAL (redacted)";

function scrubAnthropicRefusalMagic(prompt: string): string {
  if (!prompt.includes(ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL)) return prompt;
  return prompt.replaceAll(
    ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL,
    ANTHROPIC_MAGIC_STRING_REPLACEMENT,
  );
}

export async function runEmbeddedPiAgent(
  params: RunEmbeddedPiAgentParams,
): Promise<EmbeddedPiRunResult> {
  const sessionLane = resolveSessionLane(params.sessionKey?.trim() || params.sessionId);
  const globalLane = resolveGlobalLane(params.lane);
  const enqueueGlobal =
    params.enqueue ?? ((task, opts) => enqueueCommandInLane(globalLane, task, opts));
  const enqueueSession =
    params.enqueue ?? ((task, opts) => enqueueCommandInLane(sessionLane, task, opts));
  const channelHint = params.messageChannel ?? params.messageProvider;
  const resolvedToolResultFormat =
    params.toolResultFormat ??
    (channelHint
      ? isMarkdownCapableMessageChannel(channelHint)
        ? "markdown"
        : "plain"
      : "markdown");
  const isProbeSession = params.sessionId?.startsWith("probe-") ?? false;

  return enqueueSession(() =>
    enqueueGlobal(async () => {
      const started = Date.now();
      const resolvedWorkspace = resolveUserPath(params.workspaceDir);
      const prevCwd = process.cwd();

      const provider = (params.provider ?? DEFAULT_PROVIDER).trim() || DEFAULT_PROVIDER;
      const modelId = (params.model ?? DEFAULT_MODEL).trim() || DEFAULT_MODEL;
      const agentDir = params.agentDir ?? resolveOpenClawAgentDir();
      const fallbackConfigured =
        (params.config?.agents?.defaults?.model?.fallbacks?.length ?? 0) > 0;
      await ensureOpenClawModelsJson(params.config, agentDir);
```

**File:** src/channels/registry.ts (L1-100)
```typescript
import type { ChannelMeta } from "./plugins/types.js";
import type { ChannelId } from "./plugins/types.js";
import { requireActivePluginRegistry } from "../plugins/runtime.js";

// Channel docking: add new core channels here (order + meta + aliases), then
// register the plugin in its extension entrypoint and keep protocol IDs in sync.
export const CHAT_CHANNEL_ORDER = [
  "telegram",
  "whatsapp",
  "discord",
  "googlechat",
  "slack",
  "signal",
  "imessage",
] as const;

export type ChatChannelId = (typeof CHAT_CHANNEL_ORDER)[number];

export const CHANNEL_IDS = [...CHAT_CHANNEL_ORDER] as const;

export const DEFAULT_CHAT_CHANNEL: ChatChannelId = "whatsapp";

export type ChatChannelMeta = ChannelMeta;

const WEBSITE_URL = "https://openclaw.ai";

const CHAT_CHANNEL_META: Record<ChatChannelId, ChannelMeta> = {
  telegram: {
    id: "telegram",
    label: "Telegram",
    selectionLabel: "Telegram (Bot API)",
    detailLabel: "Telegram Bot",
    docsPath: "/channels/telegram",
    docsLabel: "telegram",
    blurb: "simplest way to get started — register a bot with @BotFather and get going.",
    systemImage: "paperplane",
    selectionDocsPrefix: "",
    selectionDocsOmitLabel: true,
    selectionExtras: [WEBSITE_URL],
  },
  whatsapp: {
    id: "whatsapp",
    label: "WhatsApp",
    selectionLabel: "WhatsApp (QR link)",
    detailLabel: "WhatsApp Web",
    docsPath: "/channels/whatsapp",
    docsLabel: "whatsapp",
    blurb: "works with your own number; recommend a separate phone + eSIM.",
    systemImage: "message",
  },
  discord: {
    id: "discord",
    label: "Discord",
    selectionLabel: "Discord (Bot API)",
    detailLabel: "Discord Bot",
    docsPath: "/channels/discord",
    docsLabel: "discord",
    blurb: "very well supported right now.",
    systemImage: "bubble.left.and.bubble.right",
  },
  googlechat: {
    id: "googlechat",
    label: "Google Chat",
    selectionLabel: "Google Chat (Chat API)",
    detailLabel: "Google Chat",
    docsPath: "/channels/googlechat",
    docsLabel: "googlechat",
    blurb: "Google Workspace Chat app with HTTP webhook.",
    systemImage: "message.badge",
  },
  slack: {
    id: "slack",
    label: "Slack",
    selectionLabel: "Slack (Socket Mode)",
    detailLabel: "Slack Bot",
    docsPath: "/channels/slack",
    docsLabel: "slack",
    blurb: "supported (Socket Mode).",
    systemImage: "number",
  },
  signal: {
    id: "signal",
    label: "Signal",
    selectionLabel: "Signal (signal-cli)",
    detailLabel: "Signal REST",
    docsPath: "/channels/signal",
    docsLabel: "signal",
    blurb: 'signal-cli linked device; more setup (David Reagans: "Hop on Discord.").',
    systemImage: "antenna.radiowaves.left.and.right",
  },
  imessage: {
    id: "imessage",
    label: "iMessage",
    selectionLabel: "iMessage (imsg)",
    detailLabel: "iMessage",
    docsPath: "/channels/imessage",
    docsLabel: "imessage",
    blurb: "this is still a work in progress.",
    systemImage: "message.fill",
  },
```

**File:** src/plugins/loader.ts (L1-100)
```typescript
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createJiti } from "jiti";

import type { OpenClawConfig } from "../config/config.js";
import type { GatewayRequestHandler } from "../gateway/server-methods/types.js";
import { createSubsystemLogger } from "../logging/subsystem.js";
import { resolveUserPath } from "../utils.js";
import { discoverOpenClawPlugins } from "./discovery.js";
import { loadPluginManifestRegistry } from "./manifest-registry.js";
import {
  normalizePluginsConfig,
  resolveEnableState,
  resolveMemorySlotDecision,
  type NormalizedPluginsConfig,
} from "./config-state.js";
import { initializeGlobalHookRunner } from "./hook-runner-global.js";
import { clearPluginCommands } from "./commands.js";
import { createPluginRegistry, type PluginRecord, type PluginRegistry } from "./registry.js";
import { createPluginRuntime } from "./runtime/index.js";
import { setActivePluginRegistry } from "./runtime.js";
import { validateJsonSchemaValue } from "./schema-validator.js";
import type {
  OpenClawPluginDefinition,
  OpenClawPluginModule,
  PluginDiagnostic,
  PluginLogger,
} from "./types.js";

export type PluginLoadResult = PluginRegistry;

export type PluginLoadOptions = {
  config?: OpenClawConfig;
  workspaceDir?: string;
  logger?: PluginLogger;
  coreGatewayHandlers?: Record<string, GatewayRequestHandler>;
  cache?: boolean;
  mode?: "full" | "validate";
};

const registryCache = new Map<string, PluginRegistry>();

const defaultLogger = () => createSubsystemLogger("plugins");

const resolvePluginSdkAlias = (): string | null => {
  try {
    const modulePath = fileURLToPath(import.meta.url);
    const isDistRuntime = modulePath.split(path.sep).includes("dist");
    const preferDist = process.env.VITEST || process.env.NODE_ENV === "test" || isDistRuntime;
    let cursor = path.dirname(modulePath);
    for (let i = 0; i < 6; i += 1) {
      const srcCandidate = path.join(cursor, "src", "plugin-sdk", "index.ts");
      const distCandidate = path.join(cursor, "dist", "plugin-sdk", "index.js");
      const orderedCandidates = preferDist
        ? [distCandidate, srcCandidate]
        : [srcCandidate, distCandidate];
      for (const candidate of orderedCandidates) {
        if (fs.existsSync(candidate)) return candidate;
      }
      const parent = path.dirname(cursor);
      if (parent === cursor) break;
      cursor = parent;
    }
  } catch {
    // ignore
  }
  return null;
};

function buildCacheKey(params: {
  workspaceDir?: string;
  plugins: NormalizedPluginsConfig;
}): string {
  const workspaceKey = params.workspaceDir ? resolveUserPath(params.workspaceDir) : "";
  return `${workspaceKey}::${JSON.stringify(params.plugins)}`;
}

function validatePluginConfig(params: {
  schema?: Record<string, unknown>;
  cacheKey?: string;
  value?: unknown;
}): { ok: boolean; value?: Record<string, unknown>; errors?: string[] } {
  const schema = params.schema;
  if (!schema) {
    return { ok: true, value: params.value as Record<string, unknown> | undefined };
  }
  const cacheKey = params.cacheKey ?? JSON.stringify(schema);
  const result = validateJsonSchemaValue({
    schema,
    cacheKey,
    value: params.value ?? {},
  });
  if (result.ok) {
    return { ok: true, value: params.value as Record<string, unknown> | undefined };
  }
  return { ok: false, errors: result.errors };
}

function resolvePluginModuleExport(moduleExport: unknown): {
```

**File:** src/plugins/types.ts (L1-100)
```typescript
import type { IncomingMessage, ServerResponse } from "node:http";
import type { Command } from "commander";

import type { AgentMessage } from "@mariozechner/pi-agent-core";

import type { AuthProfileCredential, OAuthCredential } from "../agents/auth-profiles/types.js";
import type { AnyAgentTool } from "../agents/tools/common.js";
import type { ChannelDock } from "../channels/dock.js";
import type { ChannelPlugin } from "../channels/plugins/types.js";
import type { OpenClawConfig } from "../config/config.js";
import type { InternalHookHandler } from "../hooks/internal-hooks.js";
import type { HookEntry } from "../hooks/types.js";
import type { ModelProviderConfig } from "../config/types.js";
import type { RuntimeEnv } from "../runtime.js";
import type { ReplyPayload } from "../auto-reply/types.js";
import type { WizardPrompter } from "../wizard/prompts.js";
import type { createVpsAwareOAuthHandlers } from "../commands/oauth-flow.js";
import type { GatewayRequestHandler } from "../gateway/server-methods/types.js";
import type { PluginRuntime } from "./runtime/types.js";

export type { PluginRuntime } from "./runtime/types.js";

export type PluginLogger = {
  debug?: (message: string) => void;
  info: (message: string) => void;
  warn: (message: string) => void;
  error: (message: string) => void;
};

export type PluginConfigUiHint = {
  label?: string;
  help?: string;
  advanced?: boolean;
  sensitive?: boolean;
  placeholder?: string;
};

export type PluginKind = "memory";

export type PluginConfigValidation =
  | { ok: true; value?: unknown }
  | { ok: false; errors: string[] };

export type OpenClawPluginConfigSchema = {
  safeParse?: (value: unknown) => {
    success: boolean;
    data?: unknown;
    error?: {
      issues?: Array<{ path: Array<string | number>; message: string }>;
    };
  };
  parse?: (value: unknown) => unknown;
  validate?: (value: unknown) => PluginConfigValidation;
  uiHints?: Record<string, PluginConfigUiHint>;
  jsonSchema?: Record<string, unknown>;
};

export type OpenClawPluginToolContext = {
  config?: OpenClawConfig;
  workspaceDir?: string;
  agentDir?: string;
  agentId?: string;
  sessionKey?: string;
  messageChannel?: string;
  agentAccountId?: string;
  sandboxed?: boolean;
};

export type OpenClawPluginToolFactory = (
  ctx: OpenClawPluginToolContext,
) => AnyAgentTool | AnyAgentTool[] | null | undefined;

export type OpenClawPluginToolOptions = {
  name?: string;
  names?: string[];
  optional?: boolean;
};

export type OpenClawPluginHookOptions = {
  entry?: HookEntry;
  name?: string;
  description?: string;
  register?: boolean;
};

export type ProviderAuthKind = "oauth" | "api_key" | "token" | "device_code" | "custom";

export type ProviderAuthResult = {
  profiles: Array<{ profileId: string; credential: AuthProfileCredential }>;
  configPatch?: Partial<OpenClawConfig>;
  defaultModel?: string;
  notes?: string[];
};

export type ProviderAuthContext = {
  config: OpenClawConfig;
  agentDir?: string;
  workspaceDir?: string;
  prompter: WizardPrompter;
  runtime: RuntimeEnv;
```

**File:** src/config/config.ts (L1-15)
```typescript
export {
  createConfigIO,
  loadConfig,
  parseConfigJson5,
  readConfigFileSnapshot,
  resolveConfigSnapshotHash,
  writeConfigFile,
} from "./io.js";
export { migrateLegacyConfig } from "./legacy-migrate.js";
export * from "./paths.js";
export * from "./runtime-overrides.js";
export * from "./types.js";
export { validateConfigObject, validateConfigObjectWithPlugins } from "./validation.js";
export { OpenClawSchema } from "./zod-schema.js";

```

**File:** src/config/types.ts (L1-30)
```typescript
// Split into focused modules to keep files small and improve edit locality.

export * from "./types.agent-defaults.js";
export * from "./types.agents.js";
export * from "./types.approvals.js";
export * from "./types.auth.js";
export * from "./types.base.js";
export * from "./types.browser.js";
export * from "./types.channels.js";
export * from "./types.openclaw.js";
export * from "./types.cron.js";
export * from "./types.discord.js";
export * from "./types.googlechat.js";
export * from "./types.gateway.js";
export * from "./types.hooks.js";
export * from "./types.imessage.js";
export * from "./types.messages.js";
export * from "./types.models.js";
export * from "./types.node-host.js";
export * from "./types.msteams.js";
export * from "./types.plugins.js";
export * from "./types.queue.js";
export * from "./types.sandbox.js";
export * from "./types.signal.js";
export * from "./types.skills.js";
export * from "./types.slack.js";
export * from "./types.telegram.js";
export * from "./types.tts.js";
export * from "./types.tools.js";
export * from "./types.whatsapp.js";
```

**File:** src/entry.ts (L122-147)
```typescript
process.argv = normalizeWindowsArgv(process.argv);

if (!ensureExperimentalWarningSuppressed()) {
  const parsed = parseCliProfileArgs(process.argv);
  if (!parsed.ok) {
    // Keep it simple; Commander will handle rich help/errors after we strip flags.
    console.error(`[openclaw] ${parsed.error}`);
    process.exit(2);
  }

  if (parsed.profile) {
    applyCliProfileEnv({ profile: parsed.profile });
    // Keep Commander and ad-hoc argv checks consistent.
    process.argv = parsed.argv;
  }

  import("./cli/run-main.js")
    .then(({ runCli }) => runCli(process.argv))
    .catch((error) => {
      console.error(
        "[openclaw] Failed to start CLI:",
        error instanceof Error ? (error.stack ?? error.message) : error,
      );
      process.exitCode = 1;
    });
}
```

**File:** src/config/io.ts (L1-50)
```typescript
import crypto from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import JSON5 from "json5";

import {
  loadShellEnvFallback,
  resolveShellEnvFallbackTimeoutMs,
  shouldDeferShellEnvFallback,
  shouldEnableShellEnvFallback,
} from "../infra/shell-env.js";
import { DuplicateAgentDirError, findDuplicateAgentDirs } from "./agent-dirs.js";
import {
  applyCompactionDefaults,
  applyContextPruningDefaults,
  applyAgentDefaults,
  applyLoggingDefaults,
  applyMessageDefaults,
  applyModelDefaults,
  applySessionDefaults,
  applyTalkApiKey,
} from "./defaults.js";
import { VERSION } from "../version.js";
import { MissingEnvVarError, resolveConfigEnvVars } from "./env-substitution.js";
import { collectConfigEnvVars } from "./env-vars.js";
import { ConfigIncludeError, resolveConfigIncludes } from "./includes.js";
import { findLegacyConfigIssues } from "./legacy.js";
import { normalizeConfigPaths } from "./normalize-paths.js";
import { resolveConfigPath, resolveDefaultConfigCandidates, resolveStateDir } from "./paths.js";
import { applyConfigOverrides } from "./runtime-overrides.js";
import type { OpenClawConfig, ConfigFileSnapshot, LegacyConfigIssue } from "./types.js";
import { validateConfigObjectWithPlugins } from "./validation.js";
import { compareOpenClawVersions } from "./version.js";

// Re-export for backwards compatibility
export { CircularIncludeError, ConfigIncludeError } from "./includes.js";
export { MissingEnvVarError } from "./env-substitution.js";

const SHELL_ENV_EXPECTED_KEYS = [
  "OPENAI_API_KEY",
  "ANTHROPIC_API_KEY",
  "ANTHROPIC_OAUTH_TOKEN",
  "GEMINI_API_KEY",
  "ZAI_API_KEY",
  "OPENROUTER_API_KEY",
  "AI_GATEWAY_API_KEY",
  "MINIMAX_API_KEY",
  "SYNTHETIC_API_KEY",
```

**File:** src/plugins/discovery.ts (L1-100)
```typescript
import fs from "node:fs";
import path from "node:path";

import { resolveConfigDir, resolveUserPath } from "../utils.js";
import { resolveBundledPluginsDir } from "./bundled-dir.js";
import {
  getPackageManifestMetadata,
  type OpenClawPackageManifest,
  type PackageManifest,
} from "./manifest.js";
import type { PluginDiagnostic, PluginOrigin } from "./types.js";

const EXTENSION_EXTS = new Set([".ts", ".js", ".mts", ".cts", ".mjs", ".cjs"]);

export type PluginCandidate = {
  idHint: string;
  source: string;
  rootDir: string;
  origin: PluginOrigin;
  workspaceDir?: string;
  packageName?: string;
  packageVersion?: string;
  packageDescription?: string;
  packageDir?: string;
  packageManifest?: OpenClawPackageManifest;
};

export type PluginDiscoveryResult = {
  candidates: PluginCandidate[];
  diagnostics: PluginDiagnostic[];
};

function isExtensionFile(filePath: string): boolean {
  const ext = path.extname(filePath);
  if (!EXTENSION_EXTS.has(ext)) return false;
  return !filePath.endsWith(".d.ts");
}

function readPackageManifest(dir: string): PackageManifest | null {
  const manifestPath = path.join(dir, "package.json");
  if (!fs.existsSync(manifestPath)) return null;
  try {
    const raw = fs.readFileSync(manifestPath, "utf-8");
    return JSON.parse(raw) as PackageManifest;
  } catch {
    return null;
  }
}

function resolvePackageExtensions(manifest: PackageManifest): string[] {
  const raw = getPackageManifestMetadata(manifest)?.extensions;
  if (!Array.isArray(raw)) return [];
  return raw.map((entry) => (typeof entry === "string" ? entry.trim() : "")).filter(Boolean);
}

function deriveIdHint(params: {
  filePath: string;
  packageName?: string;
  hasMultipleExtensions: boolean;
}): string {
  const base = path.basename(params.filePath, path.extname(params.filePath));
  const rawPackageName = params.packageName?.trim();
  if (!rawPackageName) return base;

  // Prefer the unscoped name so config keys stay stable even when the npm
  // package is scoped (example: @openclaw/voice-call -> voice-call).
  const unscoped = rawPackageName.includes("/")
    ? (rawPackageName.split("/").pop() ?? rawPackageName)
    : rawPackageName;

  if (!params.hasMultipleExtensions) return unscoped;
  return `${unscoped}/${base}`;
}

function addCandidate(params: {
  candidates: PluginCandidate[];
  seen: Set<string>;
  idHint: string;
  source: string;
  rootDir: string;
  origin: PluginOrigin;
  workspaceDir?: string;
  manifest?: PackageManifest | null;
  packageDir?: string;
}) {
  const resolved = path.resolve(params.source);
  if (params.seen.has(resolved)) return;
  params.seen.add(resolved);
  const manifest = params.manifest ?? null;
  params.candidates.push({
    idHint: params.idHint,
    source: resolved,
    rootDir: path.resolve(params.rootDir),
    origin: params.origin,
    workspaceDir: params.workspaceDir,
    packageName: manifest?.name?.trim() || undefined,
    packageVersion: manifest?.version?.trim() || undefined,
    packageDescription: manifest?.description?.trim() || undefined,
    packageDir: params.packageDir,
    packageManifest: getPackageManifestMetadata(manifest ?? undefined),
```

**File:** src/gateway/server/tls.ts (L1-100)
```typescript
import type { GatewayTlsConfig } from "../../config/types.gateway.js";
import {
  type GatewayTlsRuntime,
  loadGatewayTlsRuntime as loadGatewayTlsRuntimeConfig,
} from "../../infra/tls/gateway.js";

export type { GatewayTlsRuntime } from "../../infra/tls/gateway.js";

export async function loadGatewayTlsRuntime(
  cfg: GatewayTlsConfig | undefined,
  log?: { info?: (msg: string) => void; warn?: (msg: string) => void },
): Promise<GatewayTlsRuntime> {
  return await loadGatewayTlsRuntimeConfig(cfg, log);
}


```

**File:** src/gateway/server-channels.ts (L1-100)
```typescript
import { resolveChannelDefaultAccountId } from "../channels/plugins/helpers.js";
import { type ChannelId, getChannelPlugin, listChannelPlugins } from "../channels/plugins/index.js";
import type { ChannelAccountSnapshot } from "../channels/plugins/types.js";
import type { OpenClawConfig } from "../config/config.js";
import { formatErrorMessage } from "../infra/errors.js";
import { resetDirectoryCache } from "../infra/outbound/target-resolver.js";
import type { createSubsystemLogger } from "../logging/subsystem.js";
import { DEFAULT_ACCOUNT_ID } from "../routing/session-key.js";
import type { RuntimeEnv } from "../runtime.js";

export type ChannelRuntimeSnapshot = {
  channels: Partial<Record<ChannelId, ChannelAccountSnapshot>>;
  channelAccounts: Partial<Record<ChannelId, Record<string, ChannelAccountSnapshot>>>;
};

type SubsystemLogger = ReturnType<typeof createSubsystemLogger>;

type ChannelRuntimeStore = {
  aborts: Map<string, AbortController>;
  tasks: Map<string, Promise<unknown>>;
  runtimes: Map<string, ChannelAccountSnapshot>;
};

function createRuntimeStore(): ChannelRuntimeStore {
  return {
    aborts: new Map(),
    tasks: new Map(),
    runtimes: new Map(),
  };
}

function isAccountEnabled(account: unknown): boolean {
  if (!account || typeof account !== "object") return true;
  const enabled = (account as { enabled?: boolean }).enabled;
  return enabled !== false;
}

function resolveDefaultRuntime(channelId: ChannelId): ChannelAccountSnapshot {
  const plugin = getChannelPlugin(channelId);
  return plugin?.status?.defaultRuntime ?? { accountId: DEFAULT_ACCOUNT_ID };
}

function cloneDefaultRuntime(channelId: ChannelId, accountId: string): ChannelAccountSnapshot {
  return { ...resolveDefaultRuntime(channelId), accountId };
}

type ChannelManagerOptions = {
  loadConfig: () => OpenClawConfig;
  channelLogs: Record<ChannelId, SubsystemLogger>;
  channelRuntimeEnvs: Record<ChannelId, RuntimeEnv>;
};

export type ChannelManager = {
  getRuntimeSnapshot: () => ChannelRuntimeSnapshot;
  startChannels: () => Promise<void>;
  startChannel: (channel: ChannelId, accountId?: string) => Promise<void>;
  stopChannel: (channel: ChannelId, accountId?: string) => Promise<void>;
  markChannelLoggedOut: (channelId: ChannelId, cleared: boolean, accountId?: string) => void;
};

// Channel docking: lifecycle hooks (`plugin.gateway`) flow through this manager.
export function createChannelManager(opts: ChannelManagerOptions): ChannelManager {
  const { loadConfig, channelLogs, channelRuntimeEnvs } = opts;

  const channelStores = new Map<ChannelId, ChannelRuntimeStore>();

  const getStore = (channelId: ChannelId): ChannelRuntimeStore => {
    const existing = channelStores.get(channelId);
    if (existing) return existing;
    const next = createRuntimeStore();
    channelStores.set(channelId, next);
    return next;
  };

  const getRuntime = (channelId: ChannelId, accountId: string): ChannelAccountSnapshot => {
    const store = getStore(channelId);
    return store.runtimes.get(accountId) ?? cloneDefaultRuntime(channelId, accountId);
  };

  const setRuntime = (
    channelId: ChannelId,
    accountId: string,
    patch: ChannelAccountSnapshot,
  ): ChannelAccountSnapshot => {
    const store = getStore(channelId);
    const current = getRuntime(channelId, accountId);
    const next = { ...current, ...patch, accountId };
    store.runtimes.set(accountId, next);
    return next;
  };

  const startChannel = async (channelId: ChannelId, accountId?: string) => {
    const plugin = getChannelPlugin(channelId);
    const startAccount = plugin?.gateway?.startAccount;
    if (!startAccount) return;
    const cfg = loadConfig();
    resetDirectoryCache({ channel: channelId, accountId });
    const store = getStore(channelId);
    const accountIds = accountId ? [accountId] : plugin.config.listAccountIds(cfg);
    if (accountIds.length === 0) return;
```

**File:** src/gateway/server-cron.ts (L1-100)
```typescript
import { resolveDefaultAgentId } from "../agents/agent-scope.js";
import type { CliDeps } from "../cli/deps.js";
import { loadConfig } from "../config/config.js";
import { resolveAgentMainSessionKey } from "../config/sessions.js";
import { runCronIsolatedAgentTurn } from "../cron/isolated-agent.js";
import { appendCronRunLog, resolveCronRunLogPath } from "../cron/run-log.js";
import { CronService } from "../cron/service.js";
import { resolveCronStorePath } from "../cron/store.js";
import { runHeartbeatOnce } from "../infra/heartbeat-runner.js";
import { requestHeartbeatNow } from "../infra/heartbeat-wake.js";
import { enqueueSystemEvent } from "../infra/system-events.js";
import { getChildLogger } from "../logging.js";
import { normalizeAgentId } from "../routing/session-key.js";
import { defaultRuntime } from "../runtime.js";

export type GatewayCronState = {
  cron: CronService;
  storePath: string;
  cronEnabled: boolean;
};

export function buildGatewayCronService(params: {
  cfg: ReturnType<typeof loadConfig>;
  deps: CliDeps;
  broadcast: (event: string, payload: unknown, opts?: { dropIfSlow?: boolean }) => void;
}): GatewayCronState {
  const cronLogger = getChildLogger({ module: "cron" });
  const storePath = resolveCronStorePath(params.cfg.cron?.store);
  const cronEnabled = process.env.OPENCLAW_SKIP_CRON !== "1" && params.cfg.cron?.enabled !== false;

  const resolveCronAgent = (requested?: string | null) => {
    const runtimeConfig = loadConfig();
    const normalized =
      typeof requested === "string" && requested.trim() ? normalizeAgentId(requested) : undefined;
    const hasAgent =
      normalized !== undefined &&
      Array.isArray(runtimeConfig.agents?.list) &&
      runtimeConfig.agents.list.some(
        (entry) =>
          entry && typeof entry.id === "string" && normalizeAgentId(entry.id) === normalized,
      );
    const agentId = hasAgent ? normalized : resolveDefaultAgentId(runtimeConfig);
    return { agentId, cfg: runtimeConfig };
  };

  const cron = new CronService({
    storePath,
    cronEnabled,
    enqueueSystemEvent: (text, opts) => {
      const { agentId, cfg: runtimeConfig } = resolveCronAgent(opts?.agentId);
      const sessionKey = resolveAgentMainSessionKey({
        cfg: runtimeConfig,
        agentId,
      });
      enqueueSystemEvent(text, { sessionKey });
    },
    requestHeartbeatNow,
    runHeartbeatOnce: async (opts) => {
      const runtimeConfig = loadConfig();
      return await runHeartbeatOnce({
        cfg: runtimeConfig,
        reason: opts?.reason,
        deps: { ...params.deps, runtime: defaultRuntime },
      });
    },
    runIsolatedAgentJob: async ({ job, message }) => {
      const { agentId, cfg: runtimeConfig } = resolveCronAgent(job.agentId);
      return await runCronIsolatedAgentTurn({
        cfg: runtimeConfig,
        deps: params.deps,
        job,
        message,
        agentId,
        sessionKey: `cron:${job.id}`,
        lane: "cron",
      });
    },
    log: getChildLogger({ module: "cron", storePath }),
    onEvent: (evt) => {
      params.broadcast("cron", evt, { dropIfSlow: true });
      if (evt.action === "finished") {
        const logPath = resolveCronRunLogPath({
          storePath,
          jobId: evt.jobId,
        });
        void appendCronRunLog(logPath, {
          ts: Date.now(),
          jobId: evt.jobId,
          action: "finished",
          status: evt.status,
          error: evt.error,
          summary: evt.summary,
          runAtMs: evt.runAtMs,
          durationMs: evt.durationMs,
          nextRunAtMs: evt.nextRunAtMs,
        }).catch((err) => {
          cronLogger.warn({ err: String(err), logPath }, "cron: run log append failed");
        });
      }
    },
```

**File:** src/gateway/config-reload.ts (L1-100)
```typescript
import chokidar from "chokidar";
import { type ChannelId, listChannelPlugins } from "../channels/plugins/index.js";
import { getActivePluginRegistry } from "../plugins/runtime.js";
import type { OpenClawConfig, ConfigFileSnapshot, GatewayReloadMode } from "../config/config.js";

export type GatewayReloadSettings = {
  mode: GatewayReloadMode;
  debounceMs: number;
};

export type ChannelKind = ChannelId;

export type GatewayReloadPlan = {
  changedPaths: string[];
  restartGateway: boolean;
  restartReasons: string[];
  hotReasons: string[];
  reloadHooks: boolean;
  restartGmailWatcher: boolean;
  restartBrowserControl: boolean;
  restartCron: boolean;
  restartHeartbeat: boolean;
  restartChannels: Set<ChannelKind>;
  noopPaths: string[];
};

type ReloadRule = {
  prefix: string;
  kind: "restart" | "hot" | "none";
  actions?: ReloadAction[];
};

type ReloadAction =
  | "reload-hooks"
  | "restart-gmail-watcher"
  | "restart-browser-control"
  | "restart-cron"
  | "restart-heartbeat"
  | `restart-channel:${ChannelId}`;

const DEFAULT_RELOAD_SETTINGS: GatewayReloadSettings = {
  mode: "hybrid",
  debounceMs: 300,
};

const BASE_RELOAD_RULES: ReloadRule[] = [
  { prefix: "gateway.remote", kind: "none" },
  { prefix: "gateway.reload", kind: "none" },
  { prefix: "hooks.gmail", kind: "hot", actions: ["restart-gmail-watcher"] },
  { prefix: "hooks", kind: "hot", actions: ["reload-hooks"] },
  {
    prefix: "agents.defaults.heartbeat",
    kind: "hot",
    actions: ["restart-heartbeat"],
  },
  { prefix: "agent.heartbeat", kind: "hot", actions: ["restart-heartbeat"] },
  { prefix: "cron", kind: "hot", actions: ["restart-cron"] },
  {
    prefix: "browser",
    kind: "hot",
    actions: ["restart-browser-control"],
  },
];

const BASE_RELOAD_RULES_TAIL: ReloadRule[] = [
  { prefix: "identity", kind: "none" },
  { prefix: "wizard", kind: "none" },
  { prefix: "logging", kind: "none" },
  { prefix: "models", kind: "none" },
  { prefix: "agents", kind: "none" },
  { prefix: "tools", kind: "none" },
  { prefix: "bindings", kind: "none" },
  { prefix: "audio", kind: "none" },
  { prefix: "agent", kind: "none" },
  { prefix: "routing", kind: "none" },
  { prefix: "messages", kind: "none" },
  { prefix: "session", kind: "none" },
  { prefix: "talk", kind: "none" },
  { prefix: "skills", kind: "none" },
  { prefix: "plugins", kind: "restart" },
  { prefix: "ui", kind: "none" },
  { prefix: "gateway", kind: "restart" },
  { prefix: "discovery", kind: "restart" },
  { prefix: "canvasHost", kind: "restart" },
];

let cachedReloadRules: ReloadRule[] | null = null;
let cachedRegistry: ReturnType<typeof getActivePluginRegistry> | null = null;

function listReloadRules(): ReloadRule[] {
  const registry = getActivePluginRegistry();
  if (registry !== cachedRegistry) {
    cachedReloadRules = null;
    cachedRegistry = registry;
  }
  if (cachedReloadRules) return cachedReloadRules;
  // Channel docking: plugins contribute hot reload/no-op prefixes here.
  const channelReloadRules: ReloadRule[] = listChannelPlugins().flatMap((plugin) => [
    ...(plugin.reload?.configPrefixes ?? []).map(
      (prefix): ReloadRule => ({
```

**File:** src/gateway/server-close.ts (L1-100)
```typescript
import type { Server as HttpServer } from "node:http";
import type { WebSocketServer } from "ws";
import type { CanvasHostHandler, CanvasHostServer } from "../canvas-host/server.js";
import { type ChannelId, listChannelPlugins } from "../channels/plugins/index.js";
import { stopGmailWatcher } from "../hooks/gmail-watcher.js";
import type { HeartbeatRunner } from "../infra/heartbeat-runner.js";
import type { PluginServicesHandle } from "../plugins/services.js";

export function createGatewayCloseHandler(params: {
  bonjourStop: (() => Promise<void>) | null;
  tailscaleCleanup: (() => Promise<void>) | null;
  canvasHost: CanvasHostHandler | null;
  canvasHostServer: CanvasHostServer | null;
  stopChannel: (name: ChannelId, accountId?: string) => Promise<void>;
  pluginServices: PluginServicesHandle | null;
  cron: { stop: () => void };
  heartbeatRunner: HeartbeatRunner;
  nodePresenceTimers: Map<string, ReturnType<typeof setInterval>>;
  broadcast: (event: string, payload: unknown, opts?: { dropIfSlow?: boolean }) => void;
  tickInterval: ReturnType<typeof setInterval>;
  healthInterval: ReturnType<typeof setInterval>;
  dedupeCleanup: ReturnType<typeof setInterval>;
  agentUnsub: (() => void) | null;
  heartbeatUnsub: (() => void) | null;
  chatRunState: { clear: () => void };
  clients: Set<{ socket: { close: (code: number, reason: string) => void } }>;
  configReloader: { stop: () => Promise<void> };
  browserControl: { stop: () => Promise<void> } | null;
  wss: WebSocketServer;
  httpServer: HttpServer;
  httpServers?: HttpServer[];
}) {
  return async (opts?: { reason?: string; restartExpectedMs?: number | null }) => {
    const reasonRaw = typeof opts?.reason === "string" ? opts.reason.trim() : "";
    const reason = reasonRaw || "gateway stopping";
    const restartExpectedMs =
      typeof opts?.restartExpectedMs === "number" && Number.isFinite(opts.restartExpectedMs)
        ? Math.max(0, Math.floor(opts.restartExpectedMs))
        : null;
    if (params.bonjourStop) {
      try {
        await params.bonjourStop();
      } catch {
        /* ignore */
      }
    }
    if (params.tailscaleCleanup) {
      await params.tailscaleCleanup();
    }
    if (params.canvasHost) {
      try {
        await params.canvasHost.close();
      } catch {
        /* ignore */
      }
    }
    if (params.canvasHostServer) {
      try {
        await params.canvasHostServer.close();
      } catch {
        /* ignore */
      }
    }
    for (const plugin of listChannelPlugins()) {
      await params.stopChannel(plugin.id);
    }
    if (params.pluginServices) {
      await params.pluginServices.stop().catch(() => {});
    }
    await stopGmailWatcher();
    params.cron.stop();
    params.heartbeatRunner.stop();
    for (const timer of params.nodePresenceTimers.values()) {
      clearInterval(timer);
    }
    params.nodePresenceTimers.clear();
    params.broadcast("shutdown", {
      reason,
      restartExpectedMs,
    });
    clearInterval(params.tickInterval);
    clearInterval(params.healthInterval);
    clearInterval(params.dedupeCleanup);
    if (params.agentUnsub) {
      try {
        params.agentUnsub();
      } catch {
        /* ignore */
      }
    }
    if (params.heartbeatUnsub) {
      try {
        params.heartbeatUnsub();
      } catch {
        /* ignore */
      }
    }
    params.chatRunState.clear();
    for (const c of params.clients) {
      try {
```

**File:** src/plugins/registry.ts (L1-100)
```typescript
import type { AnyAgentTool } from "../agents/tools/common.js";
import type { ChannelDock } from "../channels/dock.js";
import type { ChannelPlugin } from "../channels/plugins/types.js";
import type {
  GatewayRequestHandler,
  GatewayRequestHandlers,
} from "../gateway/server-methods/types.js";
import { registerInternalHook } from "../hooks/internal-hooks.js";
import { resolveUserPath } from "../utils.js";
import type {
  OpenClawPluginApi,
  OpenClawPluginChannelRegistration,
  OpenClawPluginCliRegistrar,
  OpenClawPluginCommandDefinition,
  OpenClawPluginHttpHandler,
  OpenClawPluginHttpRouteHandler,
  OpenClawPluginHookOptions,
  ProviderPlugin,
  OpenClawPluginService,
  OpenClawPluginToolContext,
  OpenClawPluginToolFactory,
  PluginConfigUiHint,
  PluginDiagnostic,
  PluginLogger,
  PluginOrigin,
  PluginKind,
  PluginHookName,
  PluginHookHandlerMap,
  PluginHookRegistration as TypedPluginHookRegistration,
} from "./types.js";
import { registerPluginCommand } from "./commands.js";
import type { PluginRuntime } from "./runtime/types.js";
import type { HookEntry } from "../hooks/types.js";
import path from "node:path";
import { normalizePluginHttpPath } from "./http-path.js";

export type PluginToolRegistration = {
  pluginId: string;
  factory: OpenClawPluginToolFactory;
  names: string[];
  optional: boolean;
  source: string;
};

export type PluginCliRegistration = {
  pluginId: string;
  register: OpenClawPluginCliRegistrar;
  commands: string[];
  source: string;
};

export type PluginHttpRegistration = {
  pluginId: string;
  handler: OpenClawPluginHttpHandler;
  source: string;
};

export type PluginHttpRouteRegistration = {
  pluginId?: string;
  path: string;
  handler: OpenClawPluginHttpRouteHandler;
  source?: string;
};

export type PluginChannelRegistration = {
  pluginId: string;
  plugin: ChannelPlugin;
  dock?: ChannelDock;
  source: string;
};

export type PluginProviderRegistration = {
  pluginId: string;
  provider: ProviderPlugin;
  source: string;
};

export type PluginHookRegistration = {
  pluginId: string;
  entry: HookEntry;
  events: string[];
  source: string;
};

export type PluginServiceRegistration = {
  pluginId: string;
  service: OpenClawPluginService;
  source: string;
};

export type PluginCommandRegistration = {
  pluginId: string;
  command: OpenClawPluginCommandDefinition;
  source: string;
};

export type PluginRecord = {
  id: string;
  name: string;
  version?: string;
```

**File:** src/channels/plugins/types.plugin.ts (L1-100)
```typescript
import type { ChannelOnboardingAdapter } from "./onboarding-types.js";
import type {
  ChannelAuthAdapter,
  ChannelCommandAdapter,
  ChannelConfigAdapter,
  ChannelDirectoryAdapter,
  ChannelResolverAdapter,
  ChannelElevatedAdapter,
  ChannelGatewayAdapter,
  ChannelGroupAdapter,
  ChannelHeartbeatAdapter,
  ChannelOutboundAdapter,
  ChannelPairingAdapter,
  ChannelSecurityAdapter,
  ChannelSetupAdapter,
  ChannelStatusAdapter,
} from "./types.adapters.js";
import type {
  ChannelAgentTool,
  ChannelAgentToolFactory,
  ChannelCapabilities,
  ChannelId,
  ChannelAgentPromptAdapter,
  ChannelMentionAdapter,
  ChannelMessageActionAdapter,
  ChannelMessagingAdapter,
  ChannelMeta,
  ChannelStreamingAdapter,
  ChannelThreadingAdapter,
} from "./types.core.js";

// Channel docking: implement this contract in src/channels/plugins/<id>.ts.
// biome-ignore lint/suspicious/noExplicitAny: registry aggregates heterogeneous account types.
export type ChannelConfigUiHint = {
  label?: string;
  help?: string;
  advanced?: boolean;
  sensitive?: boolean;
  placeholder?: string;
  itemTemplate?: unknown;
};

export type ChannelConfigSchema = {
  schema: Record<string, unknown>;
  uiHints?: Record<string, ChannelConfigUiHint>;
};

export type ChannelPlugin<ResolvedAccount = any> = {
  id: ChannelId;
  meta: ChannelMeta;
  capabilities: ChannelCapabilities;
  defaults?: {
    queue?: {
      debounceMs?: number;
    };
  };
  reload?: { configPrefixes: string[]; noopPrefixes?: string[] };
  // CLI onboarding wizard hooks for this channel.
  onboarding?: ChannelOnboardingAdapter;
  config: ChannelConfigAdapter<ResolvedAccount>;
  configSchema?: ChannelConfigSchema;
  setup?: ChannelSetupAdapter;
  pairing?: ChannelPairingAdapter;
  security?: ChannelSecurityAdapter<ResolvedAccount>;
  groups?: ChannelGroupAdapter;
  mentions?: ChannelMentionAdapter;
  outbound?: ChannelOutboundAdapter;
  status?: ChannelStatusAdapter<ResolvedAccount>;
  gatewayMethods?: string[];
  gateway?: ChannelGatewayAdapter<ResolvedAccount>;
  auth?: ChannelAuthAdapter;
  elevated?: ChannelElevatedAdapter;
  commands?: ChannelCommandAdapter;
  streaming?: ChannelStreamingAdapter;
  threading?: ChannelThreadingAdapter;
  messaging?: ChannelMessagingAdapter;
  agentPrompt?: ChannelAgentPromptAdapter;
  directory?: ChannelDirectoryAdapter;
  resolver?: ChannelResolverAdapter;
  actions?: ChannelMessageActionAdapter;
  heartbeat?: ChannelHeartbeatAdapter;
  // Channel-owned agent tools (login flows, etc.).
  agentTools?: ChannelAgentToolFactory | ChannelAgentTool[];
};


```

**File:** src/plugins/providers.ts (L1-100)
```typescript
import { createSubsystemLogger } from "../logging/subsystem.js";
import { loadOpenClawPlugins, type PluginLoadOptions } from "./loader.js";
import type { ProviderPlugin } from "./types.js";

const log = createSubsystemLogger("plugins");

export function resolvePluginProviders(params: {
  config?: PluginLoadOptions["config"];
  workspaceDir?: string;
}): ProviderPlugin[] {
  const registry = loadOpenClawPlugins({
    config: params.config,
    workspaceDir: params.workspaceDir,
    logger: {
      info: (msg) => log.info(msg),
      warn: (msg) => log.warn(msg),
      error: (msg) => log.error(msg),
      debug: (msg) => log.debug(msg),
    },
  });

  return registry.providers.map((entry) => entry.provider);
}


```

**File:** src/plugins/http-registry.ts (L1-100)
```typescript
import type { IncomingMessage, ServerResponse } from "node:http";

import type { PluginHttpRouteRegistration, PluginRegistry } from "./registry.js";
import { requireActivePluginRegistry } from "./runtime.js";
import { normalizePluginHttpPath } from "./http-path.js";

export type PluginHttpRouteHandler = (
  req: IncomingMessage,
  res: ServerResponse,
) => Promise<void> | void;

export function registerPluginHttpRoute(params: {
  path?: string | null;
  fallbackPath?: string | null;
  handler: PluginHttpRouteHandler;
  pluginId?: string;
  source?: string;
  accountId?: string;
  log?: (message: string) => void;
  registry?: PluginRegistry;
}): () => void {
  const registry = params.registry ?? requireActivePluginRegistry();
  const routes = registry.httpRoutes ?? [];
  registry.httpRoutes = routes;

  const normalizedPath = normalizePluginHttpPath(params.path, params.fallbackPath);
  const suffix = params.accountId ? ` for account "${params.accountId}"` : "";
  if (!normalizedPath) {
    params.log?.(`plugin: webhook path missing${suffix}`);
    return () => {};
  }

  if (routes.some((entry) => entry.path === normalizedPath)) {
    const pluginHint = params.pluginId ? ` (${params.pluginId})` : "";
    params.log?.(`plugin: webhook path ${normalizedPath} already registered${suffix}${pluginHint}`);
    return () => {};
  }

  const entry: PluginHttpRouteRegistration = {
    path: normalizedPath,
    handler: params.handler,
    pluginId: params.pluginId,
    source: params.source,
  };
  routes.push(entry);

  return () => {
    const index = routes.indexOf(entry);
    if (index >= 0) {
      routes.splice(index, 1);
    }
  };
}


```

**File:** src/gateway/server-methods.ts (L1-100)
```typescript
import { ErrorCodes, errorShape } from "./protocol/index.js";
import { agentHandlers } from "./server-methods/agent.js";
import { agentsHandlers } from "./server-methods/agents.js";
import { browserHandlers } from "./server-methods/browser.js";
import { channelsHandlers } from "./server-methods/channels.js";
import { chatHandlers } from "./server-methods/chat.js";
import { configHandlers } from "./server-methods/config.js";
import { connectHandlers } from "./server-methods/connect.js";
import { cronHandlers } from "./server-methods/cron.js";
import { deviceHandlers } from "./server-methods/devices.js";
import { execApprovalsHandlers } from "./server-methods/exec-approvals.js";
import { healthHandlers } from "./server-methods/health.js";
import { logsHandlers } from "./server-methods/logs.js";
import { modelsHandlers } from "./server-methods/models.js";
import { nodeHandlers } from "./server-methods/nodes.js";
import { sendHandlers } from "./server-methods/send.js";
import { sessionsHandlers } from "./server-methods/sessions.js";
import { skillsHandlers } from "./server-methods/skills.js";
import { systemHandlers } from "./server-methods/system.js";
import { talkHandlers } from "./server-methods/talk.js";
import { ttsHandlers } from "./server-methods/tts.js";
import type { GatewayRequestHandlers, GatewayRequestOptions } from "./server-methods/types.js";
import { updateHandlers } from "./server-methods/update.js";
import { usageHandlers } from "./server-methods/usage.js";
import { voicewakeHandlers } from "./server-methods/voicewake.js";
import { webHandlers } from "./server-methods/web.js";
import { wizardHandlers } from "./server-methods/wizard.js";

const ADMIN_SCOPE = "operator.admin";
const READ_SCOPE = "operator.read";
const WRITE_SCOPE = "operator.write";
const APPROVALS_SCOPE = "operator.approvals";
const PAIRING_SCOPE = "operator.pairing";

const APPROVAL_METHODS = new Set(["exec.approval.request", "exec.approval.resolve"]);
const NODE_ROLE_METHODS = new Set(["node.invoke.result", "node.event", "skills.bins"]);
const PAIRING_METHODS = new Set([
  "node.pair.request",
  "node.pair.list",
  "node.pair.approve",
  "node.pair.reject",
  "node.pair.verify",
  "device.pair.list",
  "device.pair.approve",
  "device.pair.reject",
  "device.token.rotate",
  "device.token.revoke",
  "node.rename",
]);
const ADMIN_METHOD_PREFIXES = ["exec.approvals."];
const READ_METHODS = new Set([
  "health",
  "logs.tail",
  "channels.status",
  "status",
  "usage.status",
  "usage.cost",
  "tts.status",
  "tts.providers",
  "models.list",
  "agents.list",
  "agent.identity.get",
  "skills.status",
  "voicewake.get",
  "sessions.list",
  "sessions.preview",
  "cron.list",
  "cron.status",
  "cron.runs",
  "system-presence",
  "last-heartbeat",
  "node.list",
  "node.describe",
  "chat.history",
]);
const WRITE_METHODS = new Set([
  "send",
  "agent",
  "agent.wait",
  "wake",
  "talk.mode",
  "tts.enable",
  "tts.disable",
  "tts.convert",
  "tts.setProvider",
  "voicewake.set",
  "node.invoke",
  "chat.send",
  "chat.abort",
  "browser.request",
]);

function authorizeGatewayMethod(method: string, client: GatewayRequestOptions["client"]) {
  if (!client?.connect) return null;
  const role = client.connect.role ?? "operator";
  const scopes = client.connect.scopes ?? [];
  if (NODE_ROLE_METHODS.has(method)) {
    if (role === "node") return null;
    return errorShape(ErrorCodes.INVALID_REQUEST, `unauthorized role: ${role}`);
  }
```

**File:** src/agents/skills/workspace.ts (L1-100)
```typescript
import fs from "node:fs";
import path from "node:path";

import {
  formatSkillsForPrompt,
  loadSkillsFromDir,
  type Skill,
} from "@mariozechner/pi-coding-agent";

import type { OpenClawConfig } from "../../config/config.js";
import { createSubsystemLogger } from "../../logging/subsystem.js";
import { CONFIG_DIR, resolveUserPath } from "../../utils.js";
import { resolveBundledSkillsDir } from "./bundled-dir.js";
import { shouldIncludeSkill } from "./config.js";
import {
  parseFrontmatter,
  resolveOpenClawMetadata,
  resolveSkillInvocationPolicy,
} from "./frontmatter.js";
import { resolvePluginSkillDirs } from "./plugin-skills.js";
import { serializeByKey } from "./serialize.js";
import type {
  ParsedSkillFrontmatter,
  SkillEligibilityContext,
  SkillCommandSpec,
  SkillEntry,
  SkillSnapshot,
} from "./types.js";

const fsp = fs.promises;
const skillsLogger = createSubsystemLogger("skills");
const skillCommandDebugOnce = new Set<string>();

function debugSkillCommandOnce(
  messageKey: string,
  message: string,
  meta?: Record<string, unknown>,
) {
  if (skillCommandDebugOnce.has(messageKey)) return;
  skillCommandDebugOnce.add(messageKey);
  skillsLogger.debug(message, meta);
}

function filterSkillEntries(
  entries: SkillEntry[],
  config?: OpenClawConfig,
  skillFilter?: string[],
  eligibility?: SkillEligibilityContext,
): SkillEntry[] {
  let filtered = entries.filter((entry) => shouldIncludeSkill({ entry, config, eligibility }));
  // If skillFilter is provided, only include skills in the filter list.
  if (skillFilter !== undefined) {
    const normalized = skillFilter.map((entry) => String(entry).trim()).filter(Boolean);
    const label = normalized.length > 0 ? normalized.join(", ") : "(none)";
    console.log(`[skills] Applying skill filter: ${label}`);
    filtered =
      normalized.length > 0
        ? filtered.filter((entry) => normalized.includes(entry.skill.name))
        : [];
    console.log(`[skills] After filter: ${filtered.map((entry) => entry.skill.name).join(", ")}`);
  }
  return filtered;
}

const SKILL_COMMAND_MAX_LENGTH = 32;
const SKILL_COMMAND_FALLBACK = "skill";
// Discord command descriptions must be ≤100 characters
const SKILL_COMMAND_DESCRIPTION_MAX_LENGTH = 100;

function sanitizeSkillCommandName(raw: string): string {
  const normalized = raw
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  const trimmed = normalized.slice(0, SKILL_COMMAND_MAX_LENGTH);
  return trimmed || SKILL_COMMAND_FALLBACK;
}

function resolveUniqueSkillCommandName(base: string, used: Set<string>): string {
  const normalizedBase = base.toLowerCase();
  if (!used.has(normalizedBase)) return base;
  for (let index = 2; index < 1000; index += 1) {
    const suffix = `_${index}`;
    const maxBaseLength = Math.max(1, SKILL_COMMAND_MAX_LENGTH - suffix.length);
    const trimmedBase = base.slice(0, maxBaseLength);
    const candidate = `${trimmedBase}${suffix}`;
    const candidateKey = candidate.toLowerCase();
    if (!used.has(candidateKey)) return candidate;
  }
  const fallback = `${base.slice(0, Math.max(1, SKILL_COMMAND_MAX_LENGTH - 2))}_x`;
  return fallback;
}

function loadSkillEntries(
  workspaceDir: string,
  opts?: {
    config?: OpenClawConfig;
    managedSkillsDir?: string;
    bundledSkillsDir?: string;
```

**File:** src/routing/bindings.ts (L1-100)
```typescript
import { resolveDefaultAgentId } from "../agents/agent-scope.js";
import { normalizeChatChannelId } from "../channels/registry.js";
import type { OpenClawConfig } from "../config/config.js";
import type { AgentBinding } from "../config/types.agents.js";
import { normalizeAccountId, normalizeAgentId } from "./session-key.js";

function normalizeBindingChannelId(raw?: string | null): string | null {
  const normalized = normalizeChatChannelId(raw);
  if (normalized) return normalized;
  const fallback = (raw ?? "").trim().toLowerCase();
  return fallback || null;
}

export function listBindings(cfg: OpenClawConfig): AgentBinding[] {
  return Array.isArray(cfg.bindings) ? cfg.bindings : [];
}

export function listBoundAccountIds(cfg: OpenClawConfig, channelId: string): string[] {
  const normalizedChannel = normalizeBindingChannelId(channelId);
  if (!normalizedChannel) return [];
  const ids = new Set<string>();
  for (const binding of listBindings(cfg)) {
    if (!binding || typeof binding !== "object") continue;
    const match = binding.match;
    if (!match || typeof match !== "object") continue;
    const channel = normalizeBindingChannelId(match.channel);
    if (!channel || channel !== normalizedChannel) continue;
    const accountId = typeof match.accountId === "string" ? match.accountId.trim() : "";
    if (!accountId || accountId === "*") continue;
    ids.add(normalizeAccountId(accountId));
  }
  return Array.from(ids).sort((a, b) => a.localeCompare(b));
}

export function resolveDefaultAgentBoundAccountId(
  cfg: OpenClawConfig,
  channelId: string,
): string | null {
  const normalizedChannel = normalizeBindingChannelId(channelId);
  if (!normalizedChannel) return null;
  const defaultAgentId = normalizeAgentId(resolveDefaultAgentId(cfg));
  for (const binding of listBindings(cfg)) {
    if (!binding || typeof binding !== "object") continue;
    if (normalizeAgentId(binding.agentId) !== defaultAgentId) continue;
    const match = binding.match;
    if (!match || typeof match !== "object") continue;
    const channel = normalizeBindingChannelId(match.channel);
    if (!channel || channel !== normalizedChannel) continue;
    const accountId = typeof match.accountId === "string" ? match.accountId.trim() : "";
    if (!accountId || accountId === "*") continue;
    return normalizeAccountId(accountId);
  }
  return null;
}

export function buildChannelAccountBindings(cfg: OpenClawConfig) {
  const map = new Map<string, Map<string, string[]>>();
  for (const binding of listBindings(cfg)) {
    if (!binding || typeof binding !== "object") continue;
    const match = binding.match;
    if (!match || typeof match !== "object") continue;
    const channelId = normalizeBindingChannelId(match.channel);
    if (!channelId) continue;
    const accountId = typeof match.accountId === "string" ? match.accountId.trim() : "";
    if (!accountId || accountId === "*") continue;
    const agentId = normalizeAgentId(binding.agentId);
    const byAgent = map.get(channelId) ?? new Map<string, string[]>();
    const list = byAgent.get(agentId) ?? [];
    const normalizedAccountId = normalizeAccountId(accountId);
    if (!list.includes(normalizedAccountId)) list.push(normalizedAccountId);
    byAgent.set(agentId, list);
    map.set(channelId, byAgent);
  }
  return map;
}

export function resolvePreferredAccountId(params: {
  accountIds: string[];
  defaultAccountId: string;
  boundAccounts: string[];
}): string {
  if (params.boundAccounts.length > 0) return params.boundAccounts[0];
  return params.defaultAccountId;
}


```

**File:** src/agents/sandbox-agent-config.ts (L1-100)
```typescript

```

**File:** src/agents/pi-tools-agent-config.test.ts (L1-100)
```typescript
import { describe, expect, it } from "vitest";
import "./test-helpers/fast-coding-tools.js";
import type { OpenClawConfig } from "../config/config.js";
import { createOpenClawCodingTools } from "./pi-tools.js";
import type { SandboxDockerConfig } from "./sandbox.js";

describe("Agent-specific tool filtering", () => {
  it("should apply global tool policy when no agent-specific policy exists", () => {
    const cfg: OpenClawConfig = {
      tools: {
        allow: ["read", "write"],
        deny: ["bash"],
      },
      agents: {
        list: [
          {
            id: "main",
            workspace: "~/openclaw",
          },
        ],
      },
    };

    const tools = createOpenClawCodingTools({
      config: cfg,
      sessionKey: "agent:main:main",
      workspaceDir: "/tmp/test",
      agentDir: "/tmp/agent",
    });

    const toolNames = tools.map((t) => t.name);
    expect(toolNames).toContain("read");
    expect(toolNames).toContain("write");
    expect(toolNames).not.toContain("exec");
    expect(toolNames).not.toContain("apply_patch");
  });

  it("should keep global tool policy when agent only sets tools.elevated", () => {
    const cfg: OpenClawConfig = {
      tools: {
        deny: ["write"],
      },
      agents: {
        list: [
          {
            id: "main",
            workspace: "~/openclaw",
            tools: {
              elevated: {
                enabled: true,
                allowFrom: { whatsapp: ["+15555550123"] },
              },
            },
          },
        ],
      },
    };

    const tools = createOpenClawCodingTools({
      config: cfg,
      sessionKey: "agent:main:main",
      workspaceDir: "/tmp/test",
      agentDir: "/tmp/agent",
    });

    const toolNames = tools.map((t) => t.name);
    expect(toolNames).toContain("exec");
    expect(toolNames).toContain("read");
    expect(toolNames).not.toContain("write");
    expect(toolNames).not.toContain("apply_patch");
  });

  it("should allow apply_patch when exec is allow-listed and applyPatch is enabled", () => {
    const cfg: OpenClawConfig = {
      tools: {
        allow: ["read", "exec"],
        exec: {
          applyPatch: { enabled: true },
        },
      },
    };

    const tools = createOpenClawCodingTools({
      config: cfg,
      sessionKey: "agent:main:main",
      workspaceDir: "/tmp/test",
      agentDir: "/tmp/agent",
      modelProvider: "openai",
      modelId: "gpt-5.2",
    });

    const toolNames = tools.map((t) => t.name);
    expect(toolNames).toContain("read");
    expect(toolNames).toContain("exec");
    expect(toolNames).toContain("apply_patch");
  });

  it("should apply agent-specific tool policy", () => {
    const cfg: OpenClawConfig = {
      tools: {
```

**File:** docs/gateway/security/index.md (L1-100)
```markdown
---
summary: "Security considerations and threat model for running an AI gateway with shell access"
read_when:
  - Adding features that widen access or automation
---
# Security 🔒

## Quick check: `openclaw security audit`

See also: [Formal Verification (Security Models)](/security/formal-verification/)

Run this regularly (especially after changing config or exposing network surfaces):

```bash
openclaw security audit
openclaw security audit --deep
openclaw security audit --fix
```

It flags common footguns (Gateway auth exposure, browser control exposure, elevated allowlists, filesystem permissions).

`--fix` applies safe guardrails:
- Tighten `groupPolicy="open"` to `groupPolicy="allowlist"` (and per-account variants) for common channels.
- Turn `logging.redactSensitive="off"` back to `"tools"`.
- Tighten local perms (`~/.openclaw` → `700`, config file → `600`, plus common state files like `credentials/*.json`, `agents/*/agent/auth-profiles.json`, and `agents/*/sessions/sessions.json`).

Running an AI agent with shell access on your machine is... *spicy*. Here’s how to not get pwned.

OpenClaw is both a product and an experiment: you’re wiring frontier-model behavior into real messaging surfaces and real tools. **There is no “perfectly secure” setup.** The goal is to be deliberate about:
- who can talk to your bot
- where the bot is allowed to act
- what the bot can touch

Start with the smallest access that still works, then widen it as you gain confidence.

### What the audit checks (high level)

- **Inbound access** (DM policies, group policies, allowlists): can strangers trigger the bot?
- **Tool blast radius** (elevated tools + open rooms): could prompt injection turn into shell/file/network actions?
- **Network exposure** (Gateway bind/auth, Tailscale Serve/Funnel).
- **Browser control exposure** (remote nodes, relay ports, remote CDP endpoints).
- **Local disk hygiene** (permissions, symlinks, config includes, “synced folder” paths).
- **Plugins** (extensions exist without an explicit allowlist).
- **Model hygiene** (warn when configured models look legacy; not a hard block).

If you run `--deep`, OpenClaw also attempts a best-effort live Gateway probe.

## Credential storage map

Use this when auditing access or deciding what to back up:

- **WhatsApp**: `~/.openclaw/credentials/whatsapp/<accountId>/creds.json`
- **Telegram bot token**: config/env or `channels.telegram.tokenFile`
- **Discord bot token**: config/env (token file not yet supported)
- **Slack tokens**: config/env (`channels.slack.*`)
- **Pairing allowlists**: `~/.openclaw/credentials/<channel>-allowFrom.json`
- **Model auth profiles**: `~/.openclaw/agents/<agentId>/agent/auth-profiles.json`
- **Legacy OAuth import**: `~/.openclaw/credentials/oauth.json`

## Security Audit Checklist

When the audit prints findings, treat this as a priority order:

1. **Anything “open” + tools enabled**: lock down DMs/groups first (pairing/allowlists), then tighten tool policy/sandboxing.
2. **Public network exposure** (LAN bind, Funnel, missing auth): fix immediately.
3. **Browser control remote exposure**: treat it like operator access (tailnet-only, pair nodes deliberately, avoid public exposure).
4. **Permissions**: make sure state/config/credentials/auth are not group/world-readable.
5. **Plugins/extensions**: only load what you explicitly trust.
6. **Model choice**: prefer modern, instruction-hardened models for any bot with tools.

## Control UI over HTTP

The Control UI needs a **secure context** (HTTPS or localhost) to generate device
identity. If you enable `gateway.controlUi.allowInsecureAuth`, the UI falls back
to **token-only auth** and skips device pairing when device identity is omitted. This is a security
downgrade—prefer HTTPS (Tailscale Serve) or open the UI on `127.0.0.1`.

For break-glass scenarios only, `gateway.controlUi.dangerouslyDisableDeviceAuth`
disables device identity checks entirely. This is a severe security downgrade;
keep it off unless you are actively debugging and can revert quickly.

`openclaw security audit` warns when this setting is enabled.

## Reverse Proxy Configuration

If you run the Gateway behind a reverse proxy (nginx, Caddy, Traefik, etc.), you should configure `gateway.trustedProxies` for proper client IP detection.

When the Gateway detects proxy headers (`X-Forwarded-For` or `X-Real-IP`) from an address that is **not** in `trustedProxies`, it will **not** treat connections as local clients. If gateway auth is disabled, those connections are rejected. This prevents authentication bypass where proxied connections would otherwise appear to come from localhost and receive automatic trust.

```yaml
gateway:
  trustedProxies:
    - "127.0.0.1"  # if your proxy runs on localhost
  auth:
    mode: password
    password: ${OPENCLAW_GATEWAY_PASSWORD}
```

When `trustedProxies` is configured, the Gateway will use `X-Forwarded-For` headers to determine the real client IP for local client detection. Make sure your proxy overwrites (not appends to) incoming `X-Forwarded-For` headers to prevent spoofing.

```

**File:** docs/gateway/gateway-lock.md (L1-100)
```markdown
---
summary: "Gateway singleton guard using the WebSocket listener bind"
read_when:
  - Running or debugging the gateway process
  - Investigating single-instance enforcement
title: "Gateway Lock"
---

# Gateway lock

Last updated: 2025-12-11

## Why

- Ensure only one gateway instance runs per base port on the same host; additional gateways must use isolated profiles and unique ports.
- Survive crashes/SIGKILL without leaving stale lock files.
- Fail fast with a clear error when the control port is already occupied.

## Mechanism

- The gateway binds the WebSocket listener (default `ws://127.0.0.1:18789`) immediately on startup using an exclusive TCP listener.
- If the bind fails with `EADDRINUSE`, startup throws `GatewayLockError("another gateway instance is already listening on ws://127.0.0.1:<port>")`.
- The OS releases the listener automatically on any process exit, including crashes and SIGKILL—no separate lock file or cleanup step is needed.
- On shutdown the gateway closes the WebSocket server and underlying HTTP server to free the port promptly.

## Error surface

- If another process holds the port, startup throws `GatewayLockError("another gateway instance is already listening on ws://127.0.0.1:<port>")`.
- Other bind failures surface as `GatewayLockError("failed to bind gateway socket on ws://127.0.0.1:<port>: …")`.

## Operational notes

- If the port is occupied by _another_ process, the error is the same; free the port or choose another with `openclaw gateway --port <port>`.
- The macOS app still maintains its own lightweight PID guard before spawning the gateway; the runtime lock is enforced by the WebSocket bind.

```

**File:** src/agents/sandbox/docker.ts (L1-100)
```typescript
import { spawn } from "node:child_process";

import { defaultRuntime } from "../../runtime.js";
import { formatCliCommand } from "../../cli/command-format.js";
import { DEFAULT_SANDBOX_IMAGE, SANDBOX_AGENT_WORKSPACE_MOUNT } from "./constants.js";
import { readRegistry, updateRegistry } from "./registry.js";
import { computeSandboxConfigHash } from "./config-hash.js";
import { resolveSandboxAgentId, resolveSandboxScopeKey, slugifySessionKey } from "./shared.js";
import type { SandboxConfig, SandboxDockerConfig, SandboxWorkspaceAccess } from "./types.js";

const HOT_CONTAINER_WINDOW_MS = 5 * 60 * 1000;

export function execDocker(args: string[], opts?: { allowFailure?: boolean }) {
  return new Promise<{ stdout: string; stderr: string; code: number }>((resolve, reject) => {
    const child = spawn("docker", args, {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout?.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr?.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("close", (code) => {
      const exitCode = code ?? 0;
      if (exitCode !== 0 && !opts?.allowFailure) {
        reject(new Error(stderr.trim() || `docker ${args.join(" ")} failed`));
        return;
      }
      resolve({ stdout, stderr, code: exitCode });
    });
  });
}

export async function readDockerPort(containerName: string, port: number) {
  const result = await execDocker(["port", containerName, `${port}/tcp`], {
    allowFailure: true,
  });
  if (result.code !== 0) return null;
  const line = result.stdout.trim().split(/\r?\n/)[0] ?? "";
  const match = line.match(/:(\d+)\s*$/);
  if (!match) return null;
  const mapped = Number.parseInt(match[1] ?? "", 10);
  return Number.isFinite(mapped) ? mapped : null;
}

async function dockerImageExists(image: string) {
  const result = await execDocker(["image", "inspect", image], {
    allowFailure: true,
  });
  if (result.code === 0) return true;
  const stderr = result.stderr.trim();
  if (stderr.includes("No such image")) {
    return false;
  }
  throw new Error(`Failed to inspect sandbox image: ${stderr}`);
}

export async function ensureDockerImage(image: string) {
  const exists = await dockerImageExists(image);
  if (exists) return;
  if (image === DEFAULT_SANDBOX_IMAGE) {
    await execDocker(["pull", "debian:bookworm-slim"]);
    await execDocker(["tag", "debian:bookworm-slim", DEFAULT_SANDBOX_IMAGE]);
    return;
  }
  throw new Error(`Sandbox image not found: ${image}. Build or pull it first.`);
}

export async function dockerContainerState(name: string) {
  const result = await execDocker(["inspect", "-f", "{{.State.Running}}", name], {
    allowFailure: true,
  });
  if (result.code !== 0) return { exists: false, running: false };
  return { exists: true, running: result.stdout.trim() === "true" };
}

function normalizeDockerLimit(value?: string | number) {
  if (value === undefined || value === null) return undefined;
  if (typeof value === "number") {
    return Number.isFinite(value) ? String(value) : undefined;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function formatUlimitValue(
  name: string,
  value: string | number | { soft?: number; hard?: number },
) {
  if (!name.trim()) return null;
  if (typeof value === "number" || typeof value === "string") {
    const raw = String(value).trim();
    return raw ? `${name}=${raw}` : null;
  }
  const soft = typeof value.soft === "number" ? Math.max(0, value.soft) : undefined;
  const hard = typeof value.hard === "number" ? Math.max(0, value.hard) : undefined;
  if (soft === undefined && hard === undefined) return null;
```

**File:** src/config/zod-schema.ts (L1-100)
```typescript
import { z } from "zod";
import { ToolsSchema } from "./zod-schema.agent-runtime.js";
import { ApprovalsSchema } from "./zod-schema.approvals.js";
import { AgentsSchema, AudioSchema, BindingsSchema, BroadcastSchema } from "./zod-schema.agents.js";
import { HexColorSchema, ModelsConfigSchema } from "./zod-schema.core.js";
import { HookMappingSchema, HooksGmailSchema, InternalHooksSchema } from "./zod-schema.hooks.js";
import { ChannelsSchema } from "./zod-schema.providers.js";
import { CommandsSchema, MessagesSchema, SessionSchema } from "./zod-schema.session.js";

const BrowserSnapshotDefaultsSchema = z
  .object({
    mode: z.literal("efficient").optional(),
  })
  .strict()
  .optional();

const NodeHostSchema = z
  .object({
    browserProxy: z
      .object({
        enabled: z.boolean().optional(),
        allowProfiles: z.array(z.string()).optional(),
      })
      .strict()
      .optional(),
  })
  .strict()
  .optional();

export const OpenClawSchema = z
  .object({
    meta: z
      .object({
        lastTouchedVersion: z.string().optional(),
        lastTouchedAt: z.string().optional(),
      })
      .strict()
      .optional(),
    env: z
      .object({
        shellEnv: z
          .object({
            enabled: z.boolean().optional(),
            timeoutMs: z.number().int().nonnegative().optional(),
          })
          .strict()
          .optional(),
        vars: z.record(z.string(), z.string()).optional(),
      })
      .catchall(z.string())
      .optional(),
    wizard: z
      .object({
        lastRunAt: z.string().optional(),
        lastRunVersion: z.string().optional(),
        lastRunCommit: z.string().optional(),
        lastRunCommand: z.string().optional(),
        lastRunMode: z.union([z.literal("local"), z.literal("remote")]).optional(),
      })
      .strict()
      .optional(),
    diagnostics: z
      .object({
        enabled: z.boolean().optional(),
        flags: z.array(z.string()).optional(),
        otel: z
          .object({
            enabled: z.boolean().optional(),
            endpoint: z.string().optional(),
            protocol: z.union([z.literal("http/protobuf"), z.literal("grpc")]).optional(),
            headers: z.record(z.string(), z.string()).optional(),
            serviceName: z.string().optional(),
            traces: z.boolean().optional(),
            metrics: z.boolean().optional(),
            logs: z.boolean().optional(),
            sampleRate: z.number().min(0).max(1).optional(),
            flushIntervalMs: z.number().int().nonnegative().optional(),
          })
          .strict()
          .optional(),
        cacheTrace: z
          .object({
            enabled: z.boolean().optional(),
            filePath: z.string().optional(),
            includeMessages: z.boolean().optional(),
            includePrompt: z.boolean().optional(),
            includeSystem: z.boolean().optional(),
          })
          .strict()
          .optional(),
      })
      .strict()
      .optional(),
    logging: z
      .object({
        level: z
          .union([
            z.literal("silent"),
            z.literal("fatal"),
            z.literal("error"),
```

**File:** src/gateway/server-lanes.ts (L1-100)
```typescript
import type { loadConfig } from "../config/config.js";
import { resolveAgentMaxConcurrent, resolveSubagentMaxConcurrent } from "../config/agent-limits.js";
import { setCommandLaneConcurrency } from "../process/command-queue.js";
import { CommandLane } from "../process/lanes.js";

export function applyGatewayLaneConcurrency(cfg: ReturnType<typeof loadConfig>) {
  setCommandLaneConcurrency(CommandLane.Cron, cfg.cron?.maxConcurrentRuns ?? 1);
  setCommandLaneConcurrency(CommandLane.Main, resolveAgentMaxConcurrent(cfg));
  setCommandLaneConcurrency(CommandLane.Subagent, resolveSubagentMaxConcurrent(cfg));
}


```

**File:** src/agents/lanes.ts (L1-100)
```typescript
import { CommandLane } from "../process/lanes.js";

export const AGENT_LANE_NESTED = CommandLane.Nested;
export const AGENT_LANE_SUBAGENT = CommandLane.Subagent;


```

**File:** src/agents/bash-tools.exec.ts (L1-100)
```typescript
import crypto from "node:crypto";
import type { ChildProcessWithoutNullStreams } from "node:child_process";
import path from "node:path";
import type { AgentTool, AgentToolResult } from "@mariozechner/pi-agent-core";
import { Type } from "@sinclair/typebox";

import {
  type ExecAsk,
  type ExecHost,
  type ExecSecurity,
  type ExecApprovalsFile,
  addAllowlistEntry,
  evaluateShellAllowlist,
  maxAsk,
  minSecurity,
  requiresExecApproval,
  resolveSafeBins,
  recordAllowlistUse,
  resolveExecApprovals,
  resolveExecApprovalsFromFile,
} from "../infra/exec-approvals.js";
import { requestHeartbeatNow } from "../infra/heartbeat-wake.js";
import { buildNodeShellCommand } from "../infra/node-shell.js";
import {
  getShellPathFromLoginShell,
  resolveShellEnvFallbackTimeoutMs,
} from "../infra/shell-env.js";
import { enqueueSystemEvent } from "../infra/system-events.js";
import { logInfo, logWarn } from "../logger.js";
import { formatSpawnError, spawnWithFallback } from "../process/spawn-utils.js";
import {
  type ProcessSession,
  type SessionStdin,
  addSession,
  appendOutput,
  createSessionSlug,
  markBackgrounded,
  markExited,
  tail,
} from "./bash-process-registry.js";
import type { BashSandboxConfig } from "./bash-tools.shared.js";
import {
  buildDockerExecArgs,
  buildSandboxEnv,
  chunkString,
  clampNumber,
  coerceEnv,
  killSession,
  readEnvInt,
  resolveSandboxWorkdir,
  resolveWorkdir,
  truncateMiddle,
} from "./bash-tools.shared.js";
import { callGatewayTool } from "./tools/gateway.js";
import { listNodes, resolveNodeIdFromList } from "./tools/nodes-utils.js";
import { getShellConfig, sanitizeBinaryOutput } from "./shell-utils.js";
import { buildCursorPositionResponse, stripDsrRequests } from "./pty-dsr.js";
import { parseAgentSessionKey, resolveAgentIdFromSessionKey } from "../routing/session-key.js";

const DEFAULT_MAX_OUTPUT = clampNumber(
  readEnvInt("PI_BASH_MAX_OUTPUT_CHARS"),
  200_000,
  1_000,
  200_000,
);
const DEFAULT_PENDING_MAX_OUTPUT = clampNumber(
  readEnvInt("OPENCLAW_BASH_PENDING_MAX_OUTPUT_CHARS"),
  200_000,
  1_000,
  200_000,
);
const DEFAULT_PATH =
  process.env.PATH ?? "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin";
const DEFAULT_NOTIFY_TAIL_CHARS = 400;
const DEFAULT_APPROVAL_TIMEOUT_MS = 120_000;
const DEFAULT_APPROVAL_REQUEST_TIMEOUT_MS = 130_000;
const DEFAULT_APPROVAL_RUNNING_NOTICE_MS = 10_000;
const APPROVAL_SLUG_LENGTH = 8;

type PtyExitEvent = { exitCode: number; signal?: number };
type PtyListener<T> = (event: T) => void;
type PtyHandle = {
  pid: number;
  write: (data: string | Buffer) => void;
  onData: (listener: PtyListener<string>) => void;
  onExit: (listener: PtyListener<PtyExitEvent>) => void;
};
type PtySpawn = (
  file: string,
  args: string[] | string,
  options: {
    name?: string;
    cols?: number;
    rows?: number;
    cwd?: string;
    env?: Record<string, string>;
  },
) => PtyHandle;

type ExecProcessOutcome = {
```
