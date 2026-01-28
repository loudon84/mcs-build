---
name: NestJS Gateway 实施计划
overview: ""
todos:
  - id: milestone-0
    content: 创建 NestJS 项目骨架：package.json, tsconfig.json, main.ts, app.module.ts, config 模块, common 工具
    status: completed
  - id: milestone-1
    content: 实现路由控制器：health, platform, orchestrations 模块，路由映射到 orchestrator
    status: completed
    dependencies:
      - milestone-0
  - id: milestone-2
    content: 实现 JWT 认证：auth 模块，JWT 策略，认证守卫，提取 tenant_id/user_id/scopes
    status: completed
    dependencies:
      - milestone-0
  - id: milestone-3
    content: 实现策略引擎：policy 模块，YAML 加载器，策略服务，版本解析，权限验证
    status: completed
    dependencies:
      - milestone-0
  - id: milestone-4
    content: 实现限流：ratelimit 模块，Redis/内存实现，限流守卫，429 错误处理
    status: completed
    dependencies:
      - milestone-0
      - milestone-3
  - id: milestone-5
    content: 实现 Header 注入：request-id 中间件，MCS 上下文拦截器，注入 X-MCS-* headers
    status: completed
    dependencies:
      - milestone-0
      - milestone-2
  - id: milestone-6
    content: 实现代理服务：proxy 模块，HTTP 转发，超时重试，路径映射
    status: completed
    dependencies:
      - milestone-0
      - milestone-5
  - id: milestone-7
    content: 实现错误规范化：全局异常过滤器，错误码映射，统一错误响应格式
    status: completed
    dependencies:
      - milestone-0
  - id: milestone-8
    content: 实现结构化日志：日志拦截器，请求日志记录，敏感信息脱敏
    status: completed
    dependencies:
      - milestone-0
      - milestone-5
  - id: milestone-9
    content: 编写测试：认证、策略、限流、代理、端到端测试
    status: completed
    dependencies:
      - milestone-1
      - milestone-2
      - milestone-3
      - milestone-4
      - milestone-6
isProject: false
---

# NestJS Gateway 实施计划

## 概述

根据 `docs/nestjs-api.md` 需求文档，实现完整的 NestJS 网关服务，作为 MCS 平台的 Edge API，提供认证、策略执行、限流、代理转发和错误规范化功能。

## 架构设计

网关作为 Edge/BFF 层，负责：

- JWT 认证和租户/用户/权限提取
- 策略引擎（graph/version/scope 白名单）
- 限流（tenant + graph）
- 请求代理到 Orchestrator 服务
- Header 注入（X-Request-ID, X-MCS-*）
- 错误规范化

**不负责**：

- 业务 payload 解析
- LangGraph 状态机逻辑
- ERP 调用

## 实施里程碑

### Milestone 0: 项目骨架

创建 NestJS 项目基础结构：**文件清单**：

- `gateway/nestjs-api/package.json` - 项目配置，依赖：@nestjs/core, @nestjs/common, @nestjs/passport, passport-jwt, axios, js-yaml, ioredis, uuid
- `gateway/nestjs-api/tsconfig.json` - TypeScript 配置（strict mode）
- `gateway/nestjs-api/nest-cli.json` - NestJS CLI 配置
- `gateway/nestjs-api/src/main.ts` - 应用入口
- `gateway/nestjs-api/src/app.module.ts` - 根模块
- `gateway/nestjs-api/src/config/config.module.ts` - 配置模块
- `gateway/nestjs-api/src/config/config.service.ts` - 配置服务（读取环境变量）
- `gateway/nestjs-api/src/config/mcs-policy.yaml` - 策略配置文件示例
- `gateway/nestjs-api/src/common/constants.ts` - 常量定义
- `gateway/nestjs-api/src/common/types.ts` - 类型定义
- `gateway/nestjs-api/src/common/errors.ts` - 错误码定义
- `gateway/nestjs-api/src/common/logger.ts` - 日志工具
- `gateway/nestjs-api/src/common/utils/request-id.ts` - Request ID 工具
- `gateway/nestjs-api/src/common/utils/headers.ts` - Header 工具

**环境变量**：

- `MCS_POLICY_PATH` - 策略文件路径
- `ORCHESTRATOR_BASE_URL` - Orchestrator 服务地址
- `GATEWAY_TIMEOUT_MS` - 超时时间
- `JWT_JWKS_URL` 或 `JWT_PUBLIC_KEY` - JWT 验证配置
- `RATE_LIMIT_REDIS_URL` - Redis 地址（可选）
- `LOG_LEVEL` - 日志级别

### Milestone 1: 路由控制器

实现路由映射和控制器：**文件清单**：

- `gateway/nestjs-api/src/modules/health/health.controller.ts` - 健康检查
- `gateway/nestjs-api/src/modules/health/health.module.ts`
- `gateway/nestjs-api/src/modules/platform/platform.controller.ts` - Platform 路由（代理到 orchestrator /v1/platform/*）
- `gateway/nestjs-api/src/modules/platform/platform.module.ts`
- `gateway/nestjs-api/src/modules/orchestrations/orchestrations.controller.ts` - Orchestrations 路由（代理到 orchestrator /v1/orchestrations/*）
- `gateway/nestjs-api/src/modules/orchestrations/orchestrations.module.ts`

**路由映射**：

- `GET /api/mcs/v1/healthz` → 本地处理
- `GET /api/mcs/v1/platform/*` → `{ORCHESTRATOR_BASE_URL}/v1/platform/*`
- `POST /api/mcs/v1/orchestrations/:graph/run` → `{ORCHESTRATOR_BASE_URL}/v1/orchestrations/:graph/run`
- `POST /api/mcs/v1/orchestrations/:graph/replay` → `{ORCHESTRATOR_BASE_URL}/v1/orchestrations/:graph/replay`
- `POST /api/mcs/v1/orchestrations/:graph/manual-review/submit` → `{ORCHESTRATOR_BASE_URL}/v1/orchestrations/:graph/manual-review/submit`

**设计原则**：

- Controllers 保持精简：仅验证 auth/policy/ratelimit，然后代理
- 不解析业务 payload（作为 opaque JSON 处理）
- 保留上游响应体，仅规范化错误

### Milestone 2: JWT 认证

实现 JWT 验证和权限提取：**文件清单**：

- `gateway/nestjs-api/src/auth/auth.module.ts` - 认证模块
- `gateway/nestjs-api/src/auth/jwt.strategy.ts` - JWT 策略（支持 JWKS 或 public key）
- `gateway/nestjs-api/src/auth/auth.guard.ts` - 认证守卫
- `gateway/nestjs-api/src/auth/auth.types.ts` - 认证类型定义

**功能要求**：

- 读取 `Authorization: Bearer <JWT>`
- 验证签名（JWKS 或 public key）
- 提取：`tenant_id`, `sub` (user_id), `scopes` (string[] 或 space-delimited)
- 附加到请求上下文：`req.mcs.tenantId`, `req.mcs.userId`, `req.mcs.scopes`
- 错误处理：
- 缺失/无效 token → 401 `{ok:false,error_code:"UNAUTHORIZED"}`
- 缺失 tenant_id/user_id → 401 `{ok:false,error_code:"INVALID_TOKEN"}`

### Milestone 3: 策略引擎

实现策略加载和评估：**文件清单**：

- `gateway/nestjs-api/src/policy/policy.module.ts` - 策略模块
- `gateway/nestjs-api/src/policy/policy.loader.ts` - YAML 策略加载器
- `gateway/nestjs-api/src/policy/policy.service.ts` - 策略服务（评估逻辑）
- `gateway/nestjs-api/src/policy/policy.types.ts` - 策略类型定义
- `gateway/nestjs-api/src/policy/policy.errors.ts` - 策略错误

**策略格式**（YAML）：

```yaml
default:
  graphs:
        - name: sales-email
      versions: ["v1"]
      default_version: "v1"
      required_scopes: ["mcs:sales_email:run"]
      limits:
        rpm: 100
        burst: 10
tenants:
  tenant1:
    graphs:
            - name: sales-email
        versions: ["v1", "v2"]
        default_version: "v2"
routing:
  orchestrator_base_url: "http://mcs-orchestrator:8000"
  timeout_ms: 30000
  retry:
    enabled: true
    max_retries: 2
```

**功能要求**：

- `resolveGraphVersion(tenantId, graphName, requestedVersion?)` - 版本解析（优先级：X-MCS-Graph-Version header > policy default_version）
- `assertGraphAllowed(tenantId, graphName, resolvedVersion)` - 验证 graph 是否允许
- `assertScopes(requiredScopes, tokenScopes)` - 验证权限范围
- `getRateLimitConfig(tenantId, graphName)` - 获取限流配置
- 错误处理：
- Graph 不允许 → 403 `{ok:false,error_code:"PERMISSION_DENIED"}`
- Version 不允许 → 403 `{ok:false,error_code:"VERSION_NOT_ALLOWED"}`
- Scopes 不足 → 403 `{ok:false,error_code:"INSUFFICIENT_SCOPE"}`

### Milestone 4: 限流

实现基于 tenant+graph 的限流：**文件清单**：

- `gateway/nestjs-api/src/ratelimit/ratelimit.module.ts` - 限流模块
- `gateway/nestjs-api/src/ratelimit/ratelimit.guard.ts` - 限流守卫
- `gateway/nestjs-api/src/ratelimit/ratelimit.service.ts` - 限流服务（Redis 或内存实现）
- `gateway/nestjs-api/src/ratelimit/ratelimit.types.ts` - 限流类型定义

**功能要求**：

- Key = `tenantId:graphName`
- 支持 rpm（每分钟请求数）和 burst（突发）
- 优先使用 Redis（生产环境），开发环境使用内存实现
- 超出限制 → 429 `{ok:false,error_code:"RATE_LIMITED"}`
- 响应头：`Retry-After`（秒数）

### Milestone 5: Header 注入和请求上下文

实现中间件和拦截器：**文件清单**：

- `gateway/nestjs-api/src/common/middleware/request-id.middleware.ts` - Request ID 中间件
- `gateway/nestjs-api/src/common/interceptors/mcs-context.interceptor.ts` - MCS 上下文拦截器

**功能要求**：

- 确保 `X-Request-ID` 存在（缺失时生成 UUID）
- 注入到 Orchestrator 的请求头：
- `X-Request-ID`
- `X-MCS-Tenant-ID`
- `X-MCS-User-ID`
- `X-MCS-Scopes` (逗号分隔)
- `X-MCS-Graph-Name`
- `X-MCS-Graph-Version`
- `X-MCS-Client-App` (可选，来自请求头或配置)
- 保留 `traceparent`（如果存在）
- 响应中始终包含 `X-Request-ID`
- 日志中不记录原始 token，脱敏敏感 header

### Milestone 6: 代理服务

实现 HTTP 转发到 Orchestrator：**文件清单**：

- `gateway/nestjs-api/src/proxy/proxy.module.ts` - 代理模块
- `gateway/nestjs-api/src/proxy/proxy.service.ts` - 代理服务（使用 axios 或 @nestjs/axios）
- `gateway/nestjs-api/src/proxy/proxy.types.ts` - 代理类型定义

**功能要求**：

- Method/Path/Query 透传
- Body 透传（JSON）
- 超时配置（从 config 读取）
- 502/503/504 重试（最多 2 次，如果启用）
- 流式响应（可选，否则缓冲）
- 支持代理目标：
- platform endpoints
- orchestrations endpoints
- 正确映射上游路径
- 附加注入的 headers
- 不修改响应体（除错误规范化外）

### Milestone 7: 错误规范化

实现全局异常过滤器：**文件清单**：

- `gateway/nestjs-api/src/common/filters/http-exception.filter.ts` - HTTP 异常过滤器
- `gateway/nestjs-api/src/common/filters/upstream-exception.filter.ts` - 上游异常过滤器

**功能要求**：

- 转换已知错误为：`{ok:false, error_code:"...", reason:"..."}`
- 错误码映射：
- 401 → `UNAUTHORIZED`
- 403 → `PERMISSION_DENIED`
- 404 → `NOT_FOUND` (gateway route)
- 429 → `RATE_LIMITED`
- 502/503/504 → `UPSTREAM_UNAVAILABLE`
- 其他 → `INTERNAL_ERROR`
- 保留 `X-Request-ID`
- 上游错误包含：
- `upstream_status`
- `upstream_error_code`（如果响应匹配 `{error_code}` 格式）
- 生产环境不泄露堆栈跟踪

### Milestone 8: 结构化日志

实现请求日志记录：**文件清单**：

- `gateway/nestjs-api/src/common/interceptors/logging.interceptor.ts` - 日志拦截器

**功能要求**：

- 每个请求记录：
- `request_id`, `tenant_id`, `user_id`, `method`, `path`, `status`, `latency_ms`
- 不记录敏感信息：
- `Authorization` header
- 原始 email 内容/附件
- 日志与 `X-Request-ID` 关联
- 支持高 QPS 采样选项

### Milestone 9: 测试

实现测试套件：**文件清单**：

- `gateway/nestjs-api/test/auth.guard.spec.ts` - 认证守卫测试
- `gateway/nestjs-api/test/policy.service.spec.ts` - 策略服务测试
- `gateway/nestjs-api/test/ratelimit.guard.spec.ts` - 限流守卫测试
- `gateway/nestjs-api/test/proxy.service.spec.ts` - 代理服务测试
- `gateway/nestjs-api/test/e2e.spec.ts` - 端到端测试

**测试覆盖**：

- Auth guard 解析 + 缺失 claims
- Policy 允许/拒绝 + 版本解析
- 限流 429 行为
- Header 注入正确性
- 代理路径映射正确性（mock 上游）
- 错误规范化

### Milestone 10: 验收检查

确保满足所有验收标准：

- 所有路由存在并正确代理到 orchestrator
- 除 `/healthz` 外所有路由需要 JWT
- tenant/user/scopes 提取并注入
- Policy 拒绝未授权的 graph/version
- 限流按 tenant+graph 工作
- `X-Request-ID` 始终存在于响应中
- 错误规范化为 `{ok:false,error_code,reason}` 格式
- 网关不解析业务 payload
- 配置驱动的策略（YAML）

## 技术栈

- **框架**: NestJS 10.x
- **语言**: TypeScript (strict mode)
- **认证**: Passport + passport-jwt
- **HTTP 客户端**: axios 或 @nestjs/axios
- **YAML 解析**: js-yaml
- **限流存储**: ioredis (生产) / 内存 (开发)
- **测试**: Jest + @nestjs/testing

## 关键设计决策

1. **业务 payload 不解析**：网关将请求体作为 opaque JSON 透传给 Orchestrator，不进行业务逻辑验证
2. **策略驱动**：通过 YAML 配置文件管理 graph/version/scope 权限，支持租户级别覆盖
3. **版本解析优先级**：请求头 `X-MCS-Graph-Version` > 策略 `default_version`
4. **限流策略**：基于 `tenantId:graphName` 的键，支持 rpm 和 burst
5. **错误规范化**：统一错误响应格式，不泄露内部实现细节

## 文件结构

```javascript
gateway/nestjs-api/
├── src/
│   ├── main.ts
│   ├── app.module.ts
│   ├── config/
│   │   ├── config.module.ts
│   │   ├── config.service.ts
│   │   └── mcs-policy.yaml
│   ├── common/
│   │   ├── constants.ts
│   │   ├── types.ts
│   │   ├── errors.ts
│   │   ├── logger.ts
│   │   ├── utils/
│   │   │   ├── request-id.ts
│   │   │   └── headers.ts
│   │   ├── middleware/
│   │   │   └── request-id.middleware.ts
│   │   ├── interceptors/
│   │   │   ├── mcs-context.interceptor.ts
│   │   │   └── logging.interceptor.ts
│   │   └── filters/
│   │       ├── http-exception.filter.ts
│   │       └── upstream-exception.filter.ts
│   ├── auth/
│   │   ├── auth.module.ts
│   │   ├── jwt.strategy.ts
│   │   ├── auth.guard.ts
│   │   └── auth.types.ts
│   ├── policy/
│   │   ├── policy.module.ts
│   │   ├── policy.loader.ts
│   │   ├── policy.service.ts
│   │   ├── policy.types.ts
│   │   └── policy.errors.ts
│   ├── ratelimit/
│   │   ├── ratelimit.module.ts
│   │   ├── ratelimit.guard.ts
│   │   ├── ratelimit.service.ts
│   │   └── ratelimit.types.ts
│   ├── proxy/
│   │   ├── proxy.module.ts
│   │   ├── proxy.service.ts
│   │   └── proxy.types.ts
│   └── modules/
│       ├── health/
│       │   ├── health.controller.ts
│       │   └── health.module.ts
│       ├── platform/
│       │   ├── platform.controller.ts
│       │   └── platform.module.ts
│       └── orchestrations/
│           ├── orchestrations.controller.ts
│           └── orchestrations.module.ts
├── test/
│   ├── auth.guard.spec.ts
│   ├── policy.service.spec.ts
│   ├── ratelimit.guard.spec.ts
│   ├── proxy.service.spec.ts
│   └── e2e.spec.ts
├── package.json
├── tsconfig.json
├── nest-cli.json
└── README.md
```

## 实施顺序

1. **Phase 1**: Milestone 0-1（项目骨架 + 路由）
2. **Phase 2**: Milestone 2-3（认证 + 策略）
3. **Phase 3**: Milestone 4-5（限流 + Header 注入）
4. **Phase 4**: Milestone 6-7（代理 + 错误处理）
5. **Phase 5**: Milestone 8-9（日志 + 测试）
6. **Phase 6**: Milestone 10（验收）

## 注意事项

- 所有业务 payload 保持 opaque，不进行 DTO 验证
- JWT 验证支持 JWKS 和 public key 两种方式
- 策略文件支持热重载（可选）
- 限流服务需要优雅降级（Redis 不可用时使用内存）