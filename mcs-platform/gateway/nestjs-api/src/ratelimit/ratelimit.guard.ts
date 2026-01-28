import {
  Injectable,
  CanActivate,
  ExecutionContext,
} from '@nestjs/common';
import { Request } from 'express';
import { RateLimitService } from './ratelimit.service';
import { PolicyService } from '../policy/policy.service';
import { MCSRequestContext } from '../common/types';
import { RateLimitedException } from '../common/errors';

@Injectable()
export class RatelimitGuard implements CanActivate {
  constructor(
    private rateLimitService: RateLimitService,
    private policyService: PolicyService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<Request>();
    const mcsContext = (request as any).mcs as MCSRequestContext;

    if (!mcsContext?.graphName) {
      // No graph name, skip rate limiting
      return true;
    }

    const tenantId = mcsContext.tenantId;
    const graphName = mcsContext.graphName;

    // Get rate limit config from policy
    const rateLimitConfig = this.policyService.getRateLimitConfig(
      tenantId,
      graphName,
    );

    // Build rate limit key
    const key = `${tenantId}:${graphName}`;

    // Check rate limit (rpm = requests per minute)
    const windowMs = 60 * 1000; // 1 minute
    const result = await this.rateLimitService.check(
      key,
      rateLimitConfig.rpm,
      windowMs,
    );

    if (!result.allowed) {
      throw new RateLimitedException(
        `Rate limit exceeded for ${key}`,
        result.retryAfter,
      );
    }

    // Set response headers
    const response = context.switchToHttp().getResponse();
    response.setHeader('X-RateLimit-Limit', rateLimitConfig.rpm);
    response.setHeader('X-RateLimit-Remaining', result.remaining);
    response.setHeader('X-RateLimit-Reset', new Date(result.resetAt).toISOString());

    return true;
  }
}

