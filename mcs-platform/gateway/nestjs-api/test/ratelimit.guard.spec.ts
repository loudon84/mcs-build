import { Test, TestingModule } from '@nestjs/testing';
import { ExecutionContext } from '@nestjs/common';
import { RatelimitGuard } from '../src/ratelimit/ratelimit.guard';
import { RateLimitService } from '../src/ratelimit/ratelimit.service';
import { PolicyService } from '../src/policy/policy.service';
import { RateLimitedException } from '../src/common/errors';

describe('RatelimitGuard', () => {
  let guard: RatelimitGuard;
  let rateLimitService: RateLimitService;
  let policyService: PolicyService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        RatelimitGuard,
        {
          provide: RateLimitService,
          useValue: {
            check: jest.fn().mockResolvedValue({
              allowed: true,
              remaining: 99,
              resetAt: Date.now() + 60000,
            }),
          },
        },
        {
          provide: PolicyService,
          useValue: {
            getRateLimitConfig: jest.fn().mockReturnValue({
              rpm: 100,
              burst: 10,
            }),
          },
        },
      ],
    }).compile();

    guard = module.get<RatelimitGuard>(RatelimitGuard);
    rateLimitService = module.get<RateLimitService>(RateLimitService);
    policyService = module.get<PolicyService>(PolicyService);
  });

  it('should be defined', () => {
    expect(guard).toBeDefined();
  });

  it('should allow request when rate limit not exceeded', async () => {
    const request = {
      mcs: {
        tenantId: 'tenant1',
        graphName: 'sales-email',
      },
    } as any;

    const response = {
      setHeader: jest.fn(),
    } as any;

    const context = {
      switchToHttp: () => ({
        getRequest: () => request,
        getResponse: () => response,
      }),
    } as ExecutionContext;

    const result = await guard.canActivate(context);
    expect(result).toBe(true);
    expect(response.setHeader).toHaveBeenCalledWith('X-RateLimit-Limit', 100);
  });

  it('should throw RateLimitedException when limit exceeded', async () => {
    (rateLimitService.check as jest.Mock).mockResolvedValue({
      allowed: false,
      remaining: 0,
      resetAt: Date.now() + 60000,
      retryAfter: 60,
    });

    const request = {
      mcs: {
        tenantId: 'tenant1',
        graphName: 'sales-email',
      },
    } as any;

    const context = {
      switchToHttp: () => ({
        getRequest: () => request,
        getResponse: () => ({}),
      }),
    } as ExecutionContext;

    await expect(guard.canActivate(context)).rejects.toThrow(
      RateLimitedException,
    );
  });

  it('should skip rate limiting when no graph name', async () => {
    const request = {
      mcs: {},
    } as any;

    const context = {
      switchToHttp: () => ({
        getRequest: () => request,
        getResponse: () => ({}),
      }),
    } as ExecutionContext;

    const result = await guard.canActivate(context);
    expect(result).toBe(true);
    expect(rateLimitService.check).not.toHaveBeenCalled();
  });
});

