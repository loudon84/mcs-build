import { PolicyConfig, PolicyGraph, RateLimitConfig } from '../common/types';

export interface PolicyLoader {
  load(): Promise<PolicyConfig>;
  reload(): Promise<PolicyConfig>;
}

export interface PolicyEvaluator {
  resolveGraphVersion(
    tenantId: string,
    graphName: string,
    requestedVersion?: string,
  ): string;
  assertGraphAllowed(
    tenantId: string,
    graphName: string,
    version: string,
  ): void;
  assertScopes(requiredScopes: string[], tokenScopes: string[]): void;
  getRateLimitConfig(tenantId: string, graphName: string): RateLimitConfig;
  getGraphConfig(tenantId: string, graphName: string): PolicyGraph | null;
}

