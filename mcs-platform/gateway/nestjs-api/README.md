# MCS Gateway - NestJS API

MCS Platform 的 Edge API 网关，提供认证、策略执行、限流、代理转发和错误规范化功能。

## 功能特性

- **JWT 认证**: 支持 JWKS 和 Public Key 两种验证方式
- **策略引擎**: YAML 配置驱动的 graph/version/scope 权限管理
- **限流**: 基于 tenant+graph 的限流，支持 Redis 和内存存储
- **代理转发**: HTTP 请求代理到 Orchestrator 服务
- **Header 注入**: 自动注入 X-Request-ID, X-MCS-* 等请求头
- **错误规范化**: 统一的错误响应格式
- **结构化日志**: 请求日志记录，敏感信息脱敏

## 环境变量

```bash
# 策略配置
MCS_POLICY_PATH=src/config/mcs-policy.yaml

# Orchestrator 服务地址
ORCHESTRATOR_BASE_URL=http://mcs-orchestrator:8000

# 网关超时时间（毫秒）
GATEWAY_TIMEOUT_MS=30000

# JWT 验证配置（二选一）
JWT_JWKS_URL=https://your-auth-server/.well-known/jwks.json
# 或
JWT_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----\n...

# Redis 限流（可选，不配置则使用内存）
RATE_LIMIT_REDIS_URL=redis://localhost:6379

# 日志级别
LOG_LEVEL=info

# 端口
PORT=3000
```

## 安装和运行

```bash
# 安装依赖
npm install

# 开发模式
npm run start:dev

# 生产模式
npm run build
npm run start:prod
```

## API 路由

### 健康检查

```
GET /api/mcs/v1/healthz
```

### Platform 路由

```
GET /api/mcs/v1/platform/graphs
GET /api/mcs/v1/platform/graphs/:name
GET /api/mcs/v1/platform/graphs/:name/:version/schema
GET /api/mcs/v1/platform/tools
GET /api/mcs/v1/platform/tools/:name
GET /api/mcs/v1/platform/tools/:name/:version/schema
```

### Orchestrations 路由

```
POST /api/mcs/v1/orchestrations/:graph/run
POST /api/mcs/v1/orchestrations/:graph/replay
POST /api/mcs/v1/orchestrations/:graph/manual-review/submit
```

## 策略配置

策略配置文件位于 `src/config/mcs-policy.yaml`，支持：

- 默认 graph 配置
- 租户级别覆盖
- 版本控制
- 权限范围要求
- 限流配置

## 测试

```bash
# 单元测试
npm test

# E2E 测试
npm run test:e2e

# 测试覆盖率
npm run test:cov
```

## 架构设计

网关作为 Edge/BFF 层，负责：

- ✅ JWT 认证和租户/用户/权限提取
- ✅ 策略引擎（graph/version/scope 白名单）
- ✅ 限流（tenant + graph）
- ✅ 请求代理到 Orchestrator 服务
- ✅ Header 注入（X-Request-ID, X-MCS-*）
- ✅ 错误规范化

**不负责**：

- ❌ 业务 payload 解析
- ❌ LangGraph 状态机逻辑
- ❌ ERP 调用

## 许可证

[待定]

