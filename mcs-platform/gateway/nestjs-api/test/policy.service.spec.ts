import { Test, TestingModule } from '@nestjs/testing';
import { PolicyService } from '../src/policy/policy.service';
import { YamlPolicyLoader } from '../src/policy/policy.loader';
import { ConfigService } from '../src/config/config.service';
import {
  GraphNotAllowedError,
  GraphVersionNotAllowedError,
  InsufficientScopesError,
} from '../src/policy/policy.errors';

describe('PolicyService', () => {
  let service: PolicyService;
  let loader: YamlPolicyLoader;

  const mockPolicy = {
    default: {
      graphs: [
        {
          name: 'sales-email',
          versions: ['v1'],
          default_version: 'v1',
          required_scopes: ['mcs:sales_email:run'],
          limits: {
            rpm: 100,
            burst: 10,
          },
        },
      ],
    },
    tenants: {
      tenant1: {
        graphs: [
          {
            name: 'sales-email',
            versions: ['v1', 'v2'],
            default_version: 'v2',
            required_scopes: ['mcs:sales_email:run'],
            limits: {
              rpm: 200,
              burst: 20,
            },
          },
        ],
      },
    },
    routing: {
      orchestrator_base_url: 'http://localhost:8000',
      timeout_ms: 30000,
      retry: {
        enabled: true,
        max_retries: 2,
      },
    },
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [
        PolicyService,
        {
          provide: 'PolicyLoader',
          useValue: {
            load: jest.fn().mockResolvedValue(mockPolicy),
            policyCache: mockPolicy,
          },
        },
        {
          provide: ConfigService,
          useValue: {
            policyPath: 'src/config/mcs-policy.yaml',
            isProduction: false,
          },
        },
      ],
    }).compile();

    service = module.get<PolicyService>(PolicyService);
    loader = module.get('PolicyLoader');
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('resolveGraphVersion', () => {
    it('should return default version when no version requested', () => {
      const version = service.resolveGraphVersion('tenant1', 'sales-email');
      expect(version).toBe('v2'); // tenant1 default
    });

    it('should return requested version when allowed', () => {
      const version = service.resolveGraphVersion(
        'tenant1',
        'sales-email',
        'v1',
      );
      expect(version).toBe('v1');
    });

    it('should throw when version not allowed', () => {
      expect(() => {
        service.resolveGraphVersion('tenant1', 'sales-email', 'v3');
      }).toThrow(GraphVersionNotAllowedError);
    });

    it('should throw when graph not allowed', () => {
      expect(() => {
        service.resolveGraphVersion('tenant1', 'unknown-graph');
      }).toThrow(GraphNotAllowedError);
    });
  });

  describe('assertScopes', () => {
    it('should pass when all required scopes are present', () => {
      expect(() => {
        service.assertScopes(['mcs:sales_email:run'], ['mcs:sales_email:run']);
      }).not.toThrow();
    });

    it('should throw when scopes are insufficient', () => {
      expect(() => {
        service.assertScopes(
          ['mcs:sales_email:run', 'mcs:sales_email:admin'],
          ['mcs:sales_email:run'],
        );
      }).toThrow(InsufficientScopesError);
    });
  });

  describe('getRateLimitConfig', () => {
    it('should return rate limit config for tenant', () => {
      const config = service.getRateLimitConfig('tenant1', 'sales-email');
      expect(config.rpm).toBe(200);
      expect(config.burst).toBe(20);
    });

    it('should return default rate limit config', () => {
      const config = service.getRateLimitConfig('default-tenant', 'sales-email');
      expect(config.rpm).toBe(100);
      expect(config.burst).toBe(10);
    });
  });
});

