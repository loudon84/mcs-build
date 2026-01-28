import { Injectable, OnModuleInit } from '@nestjs/common';
import { PolicyLoader } from './policy.loader';
import { PolicyEvaluator } from './policy.types';
import { YamlPolicyLoader } from './policy.loader';
import {
  GraphNotAllowedError,
  GraphVersionNotAllowedError,
  InsufficientScopesError,
} from './policy.errors';
import { PolicyGraph, RateLimitConfig } from '../common/types';

@Injectable()
export class PolicyService implements PolicyEvaluator, OnModuleInit {
  constructor(private loader: PolicyLoader) {}

  async onModuleInit() {
    await this.loader.load();
  }

  private async getPolicy() {
    return this.loader.load();
  }

  private getGraphConfig(
    tenantId: string,
    graphName: string,
  ): PolicyGraph | null {
    return this.getGraphConfigSync(tenantId, graphName);
  }

  private getGraphConfigSync(
    tenantId: string,
    graphName: string,
  ): PolicyGraph | null {
    // This is a synchronous helper - in real implementation, we'd need to make this async
    // For now, we'll use a cached approach
    const loader = this.loader as YamlPolicyLoader;
    const policy = (loader as any).policyCache;
    if (!policy) {
      return null;
    }

    // Check tenant-specific config first
    if (policy.tenants?.[tenantId]?.graphs) {
      const tenantGraph = policy.tenants[tenantId].graphs.find(
        (g: PolicyGraph) => g.name === graphName,
      );
      if (tenantGraph) {
        return tenantGraph;
      }
    }

    // Fall back to default
    if (policy.default?.graphs) {
      const defaultGraph = policy.default.graphs.find(
        (g: PolicyGraph) => g.name === graphName,
      );
      if (defaultGraph) {
        return defaultGraph;
      }
    }

    return null;
  }

  resolveGraphVersion(
    tenantId: string,
    graphName: string,
    requestedVersion?: string,
  ): string {
    const graphConfig = this.getGraphConfigSync(tenantId, graphName);
    if (!graphConfig) {
      throw new GraphNotAllowedError(graphName, tenantId);
    }

    // Priority: requestedVersion > default_version
    if (requestedVersion) {
      if (graphConfig.versions.includes(requestedVersion)) {
        return requestedVersion;
      }
      throw new GraphVersionNotAllowedError(graphName, requestedVersion, tenantId);
    }

    return graphConfig.default_version;
  }

  assertGraphAllowed(tenantId: string, graphName: string, version: string): void {
    const graphConfig = this.getGraphConfigSync(tenantId, graphName);
    if (!graphConfig) {
      throw new GraphNotAllowedError(graphName, tenantId);
    }

    if (!graphConfig.versions.includes(version)) {
      throw new GraphVersionNotAllowedError(graphName, version, tenantId);
    }
  }

  assertScopes(requiredScopes: string[], tokenScopes: string[]): void {
    const hasAllScopes = requiredScopes.every((scope) =>
      tokenScopes.includes(scope),
    );

    if (!hasAllScopes) {
      throw new InsufficientScopesError(requiredScopes, tokenScopes);
    }
  }

  getRateLimitConfig(tenantId: string, graphName: string): RateLimitConfig {
    const graphConfig = this.getGraphConfigSync(tenantId, graphName);
    if (!graphConfig) {
      throw new GraphNotAllowedError(graphName, tenantId);
    }

    return graphConfig.limits;
  }

  getGraphConfig(tenantId: string, graphName: string): PolicyGraph | null {
    return this.getGraphConfigSync(tenantId, graphName);
  }
}

