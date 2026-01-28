# File: gateway/nestjs-api/mcs-edge.plan
# Purpose: Minimal Viable NestJS Gateway (MCS Edge API)
# Scope: Auth + Policy + RateLimit + Proxy + Header Injection + Error Normalization
# Note: Business payload is opaque; do NOT parse/order/ERP/Dify logic here.

================================================================================
MILESTONE 0 — Project Skeleton (create folders/files)
================================================================================
TODO: Create NestJS project (if not exists) under /gateway/nestjs-api
TODO: Ensure TypeScript strict mode enabled
TODO: Add config folder and policy YAML loader
TODO: Add basic health endpoint

FILES TO CREATE:
- gateway/nestjs-api/src/main.ts
- gateway/nestjs-api/src/app.module.ts
- gateway/nestjs-api/src/config/config.module.ts
- gateway/nestjs-api/src/config/config.service.ts
- gateway/nestjs-api/src/config/mcs-policy.yaml
- gateway/nestjs-api/src/common/constants.ts
- gateway/nestjs-api/src/common/types.ts
- gateway/nestjs-api/src/common/errors.ts
- gateway/nestjs-api/src/common/logger.ts
- gateway/nestjs-api/src/common/utils/request-id.ts
- gateway/nestjs-api/src/common/utils/headers.ts

ENV VARS REQUIRED:
- MCS_POLICY_PATH=src/config/mcs-policy.yaml
- ORCHESTRATOR_BASE_URL=http://mcs-orchestrator:8000
- GATEWAY_TIMEOUT_MS=30000
- JWT_JWKS_URL=... or JWT_PUBLIC_KEY=...
- RATE_LIMIT_REDIS_URL=... (optional)
- LOG_LEVEL=info

================================================================================
MILESTONE 1 — Routing Table (Controllers)
================================================================================
TODO: Implement minimal route map with version prefix /api/mcs/v1

ROUTES (External):
1) GET  /api/mcs/v1/healthz
2) GET  /api/mcs/v1/platform/graphs
3) GET  /api/mcs/v1/platform/graphs/:name
4) GET  /api/mcs/v1/platform/graphs/:name/:version/schema
5) GET  /api/mcs/v1/platform/tools
6) GET  /api/mcs/v1/platform/tools/:name
7) GET  /api/mcs/v1/platform/tools/:name/:version/schema
8) POST /api/mcs/v1/orchestrations/:graph/run
9) POST /api/mcs/v1/orchestrations/:graph/replay
10)POST /api/mcs/v1/orchestrations/:graph/manual-review/submit
11)POST /api/mcs/v1/orchestrations/:graph/resume (optional, behind feature flag)

UPSTREAM (Orchestrator) MAPPING:
- /api/mcs/v1/platform/*  -> {ORCHESTRATOR_BASE_URL}/v1/platform/*
- /api/mcs/v1/orchestrations/:graph/* -> {ORCHESTRATOR_BASE_URL}/v1/orchestrations/:graph/*

FILES TO CREATE:
- gateway/nestjs-api/src/modules/health/health.controller.ts
- gateway/nestjs-api/src/modules/platform/platform.controller.ts
- gateway/nestjs-api/src/modules/orchestrations/orchestrations.controller.ts
- gateway/nestjs-api/src/modules/platform/platform.module.ts
- gateway/nestjs-api/src/modules/orchestrations/orchestrations.module.ts
- gateway/nestjs-api/src/modules/health/health.module.ts

TODO per controller:
- Controllers MUST be thin: validate auth/policy/ratelimit then proxy
- Do NOT deserialize body into business DTOs (treat as opaque JSON)
- Preserve response body from upstream; normalize errors only

================================================================================
MILESTONE 2 — Auth (JWT Validation + Tenant/User/Scopes Extraction)
================================================================================
TODO: Add AuthGuard that:
- Reads Authorization: Bearer <JWT>
- Validates signature (JWKS or public key)
- Extracts:
  - tenant_id
  - sub as user_id
  - scopes (space-delimited "scope" or array "scopes")
- Attaches to request context

FILES TO CREATE:
- gateway/nestjs-api/src/auth/auth.module.ts
- gateway/nestjs-api/src/auth/jwt.strategy.ts
- gateway/nestjs-api/src/auth/auth.guard.ts
- gateway/nestjs-api/src/auth/auth.types.ts

TODO:
- Reject missing/invalid token -> 401 with {ok:false,error_code:"UNAUTHORIZED"}
- Reject missing tenant_id/user_id -> 401 with {ok:false,error_code:"INVALID_TOKEN"}
- Ensure request context includes:
  - req.mcs.tenantId
  - req.mcs.userId
  - req.mcs.scopes (string[])
- Add unit tests for token parsing (mock keys)

================================================================================
MILESTONE 3 — Policy Engine (Graph/Version/Scope allowlist)
================================================================================
TODO: Implement policy loader + evaluator
- Load YAML policy on boot (and optionally reload on interval)
- Provide functions:
  - resolveGraphVersion(tenantId, graphName, requestedVersion?)
  - assertGraphAllowed(tenantId, graphName, resolvedVersion)
  - assertScopes(requiredScopes, tokenScopes)
  - getRateLimitConfig(tenantId, graphName)

FILES TO CREATE:
- gateway/nestjs-api/src/policy/policy.module.ts
- gateway/nestjs-api/src/policy/policy.loader.ts
- gateway/nestjs-api/src/policy/policy.service.ts
- gateway/nestjs-api/src/policy/policy.types.ts
- gateway/nestjs-api/src/policy/policy.errors.ts

POLICY FORMAT (must support):
- default.graphs[]: name, versions[], default_version, required_scopes[], limits{rpm,burst}
- tenants.<tenantId>.graphs[] overrides
- routing.orchestrator_base_url, timeout_ms, retry{...}

TODO:
- If graph not allowed -> 403 {ok:false,error_code:"PERMISSION_DENIED"}
- If version not allowed -> 403 {ok:false,error_code:"VERSION_NOT_ALLOWED"}
- If scopes missing -> 403 {ok:false,error_code:"INSUFFICIENT_SCOPE"}
- Graph version resolution precedence:
  1) X-MCS-Graph-Version header (requested)
  2) policy default_version

================================================================================
MILESTONE 4 — Rate Limiting (tenant+graph)
================================================================================
TODO: Implement minimal rate limiter:
- Key = tenantId + ":" + graphName
- Enforce rpm + burst
- Prefer Redis-backed (production); fallback in-memory for dev

FILES TO CREATE:
- gateway/nestjs-api/src/ratelimit/ratelimit.module.ts
- gateway/nestjs-api/src/ratelimit/ratelimit.guard.ts
- gateway/nestjs-api/src/ratelimit/ratelimit.service.ts
- gateway/nestjs-api/src/ratelimit/ratelimit.types.ts

TODO:
- Exceed limit -> 429 {ok:false,error_code:"RATE_LIMITED"}
- Add response header: Retry-After (seconds) if possible

================================================================================
MILESTONE 5 — Header Injection + Request Context
================================================================================
TODO: Implement middleware/interceptor to:
- Ensure X-Request-ID exists (generate UUID if missing)
- Inject outbound headers to Orchestrator:
  - X-Request-ID
  - X-MCS-Tenant-ID
  - X-MCS-User-ID
  - X-MCS-Scopes (comma-separated)
  - X-MCS-Graph-Name
  - X-MCS-Graph-Version
  - X-MCS-Client-App (optional from incoming header or configured)
- Preserve traceparent if present

FILES TO CREATE:
- gateway/nestjs-api/src/common/middleware/request-id.middleware.ts
- gateway/nestjs-api/src/common/interceptors/mcs-context.interceptor.ts

TODO:
- Always return X-Request-ID in response headers
- Never log raw token; redact sensitive headers

================================================================================
MILESTONE 6 — Proxy Service (HTTP forward to Orchestrator)
================================================================================
TODO: Implement proxy forwarder:
- Method/Path/Query passthrough
- Body passthrough (JSON)
- Timeout from config
- Retry on 502/503/504 if enabled (max 2)
- Stream response if possible (optional; otherwise buffer)

FILES TO CREATE:
- gateway/nestjs-api/src/proxy/proxy.module.ts
- gateway/nestjs-api/src/proxy/proxy.service.ts
- gateway/nestjs-api/src/proxy/proxy.types.ts

TODO:
- Support these proxy targets:
  - platform endpoints
  - orchestrations endpoints
- Ensure correct upstream path mapping
- Attach injected headers
- Do not mutate response body (except error normalization below)

================================================================================
MILESTONE 7 — Error Normalization (consistent error payload)
================================================================================
TODO: Implement global exception filter:
- Convert known errors into:
  { ok:false, error_code:"...", reason:"..." }
- Map:
  - 401 -> UNAUTHORIZED
  - 403 -> PERMISSION_DENIED
  - 404 -> NOT_FOUND (gateway route)
  - 429 -> RATE_LIMITED
  - 502/503/504 -> UPSTREAM_UNAVAILABLE
  - generic -> INTERNAL_ERROR

FILES TO CREATE:
- gateway/nestjs-api/src/common/filters/http-exception.filter.ts
- gateway/nestjs-api/src/common/filters/upstream-exception.filter.ts

TODO:
- Preserve X-Request-ID
- For upstream errors, include minimal info:
  - upstream_status
  - (optional) upstream_error_code if response matches {error_code}
- Do not leak stack traces in prod

================================================================================
MILESTONE 8 — Logging (structured, minimal, audited fields)
================================================================================
TODO: Implement structured logging:
- Log per request:
  - request_id, tenant_id, user_id, method, path, status, latency_ms
- Do NOT log sensitive:
  - Authorization
  - raw email content / attachments

FILES TO CREATE:
- gateway/nestjs-api/src/common/interceptors/logging.interceptor.ts

TODO:
- Correlate logs with X-Request-ID
- Add sampling option for high QPS

================================================================================
MILESTONE 9 — Tests (minimal)
================================================================================
TODO: Add test suite for:
- Auth guard parsing + missing claims
- Policy allow/deny + version resolution
- Rate limit 429 behavior
- Header injection correctness
- Proxy path mapping correctness (mock upstream)
- Error normalization

FILES TO CREATE:
- gateway/nestjs-api/test/auth.guard.spec.ts
- gateway/nestjs-api/test/policy.service.spec.ts
- gateway/nestjs-api/test/ratelimit.guard.spec.ts
- gateway/nestjs-api/test/proxy.service.spec.ts
- gateway/nestjs-api/test/e2e.spec.ts

================================================================================
MILESTONE 10 — Acceptance Checklist
================================================================================
TODO: Confirm these acceptance criteria:
- All routes exist and proxy correctly to orchestrator
- JWT required for all except /healthz
- tenant/user/scopes extracted and injected
- Policy denies unauthorized graph/version
- Rate limiting works per tenant+graph
- X-Request-ID always present in response
- Errors normalized into {ok:false,error_code,reason}
- No business payload parsing in gateway
- Configuration driven policy via YAML
