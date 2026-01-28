import { Test, TestingModule } from '@nestjs/testing';
import { ExecutionContext, UnauthorizedException } from '@nestjs/common';
import { JwtAuthGuard } from '../src/auth/auth.guard';
import { JwtStrategy } from '../src/auth/jwt.strategy';
import { ConfigService } from '../src/config/config.service';

describe('JwtAuthGuard', () => {
  let guard: JwtAuthGuard;
  let strategy: JwtStrategy;
  let configService: ConfigService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        JwtAuthGuard,
        {
          provide: JwtStrategy,
          useValue: {
            validate: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {
            jwtJwksUrl: undefined,
            jwtPublicKey: 'test-public-key',
          },
        },
      ],
    }).compile();

    guard = module.get<JwtAuthGuard>(JwtAuthGuard);
    strategy = module.get<JwtStrategy>(JwtStrategy);
    configService = module.get<ConfigService>(ConfigService);
  });

  it('should be defined', () => {
    expect(guard).toBeDefined();
  });

  it('should throw UnauthorizedException when user is missing', () => {
    const context = {
      switchToHttp: () => ({
        getRequest: () => ({
          headers: {},
        }),
      }),
    } as ExecutionContext;

    expect(() => {
      guard.handleRequest(null, null, null, context);
    }).toThrow(UnauthorizedException);
  });

  it('should attach MCS context when user is valid', () => {
    const request = {
      headers: {},
    } as any;

    const context = {
      switchToHttp: () => ({
        getRequest: () => request,
      }),
    } as ExecutionContext;

    const user = {
      sub: 'user123',
      tenant_id: 'tenant1',
      scopes: ['scope1', 'scope2'],
    };

    guard.handleRequest(null, user, null, context);

    expect(request.mcs).toBeDefined();
    expect(request.mcs.userId).toBe('user123');
    expect(request.mcs.tenantId).toBe('tenant1');
    expect(request.mcs.scopes).toEqual(['scope1', 'scope2']);
  });
});

