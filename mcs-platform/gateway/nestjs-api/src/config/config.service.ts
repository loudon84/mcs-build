import { Injectable } from '@nestjs/common';

@Injectable()
export class ConfigService {
  get policyPath(): string {
    return process.env.MCS_POLICY_PATH || 'src/config/mcs-policy.yaml';
  }

  get orchestratorBaseUrl(): string {
    return process.env.ORCHESTRATOR_BASE_URL || 'http://localhost:8000';
  }

  get gatewayTimeoutMs(): number {
    return parseInt(process.env.GATEWAY_TIMEOUT_MS || '30000', 10);
  }

  get jwtJwksUrl(): string | undefined {
    return process.env.JWT_JWKS_URL;
  }

  get jwtPublicKey(): string | undefined {
    return process.env.JWT_PUBLIC_KEY;
  }

  get rateLimitRedisUrl(): string | undefined {
    return process.env.RATE_LIMIT_REDIS_URL;
  }

  get logLevel(): string {
    return process.env.LOG_LEVEL || 'info';
  }

  get nodeEnv(): string {
    return process.env.NODE_ENV || 'development';
  }

  get isProduction(): boolean {
    return this.nodeEnv === 'production';
  }
}

