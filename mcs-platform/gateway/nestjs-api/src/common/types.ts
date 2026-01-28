/**
 * Common type definitions for MCS Gateway
 */

export interface MCSRequestContext {
  tenantId: string;
  userId: string;
  scopes: string[];
  requestId: string;
  graphName?: string;
  graphVersion?: string;
}

export interface ErrorResponse {
  ok: false;
  error_code: string;
  reason: string;
  upstream_status?: number;
  upstream_error_code?: string;
}

export interface PolicyGraph {
  name: string;
  versions: string[];
  default_version: string;
  required_scopes: string[];
  limits: {
    rpm: number;
    burst: number;
  };
}

export interface PolicyConfig {
  default: {
    graphs: PolicyGraph[];
  };
  tenants: Record<string, {
    graphs: PolicyGraph[];
  }>;
  routing: {
    orchestrator_base_url: string;
    timeout_ms: number;
    retry: {
      enabled: boolean;
      max_retries: number;
    };
  };
}

export interface RateLimitConfig {
  rpm: number;
  burst: number;
}

export interface JWTPayload {
  sub: string; // user_id
  tenant_id?: string;
  scope?: string; // space-delimited
  scopes?: string[]; // array format
  [key: string]: any;
}

