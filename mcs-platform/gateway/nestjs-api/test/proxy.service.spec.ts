import { Test, TestingModule } from '@nestjs/testing';
import { HttpService } from '@nestjs/axios';
import { of, throwError } from 'rxjs';
import { AxiosResponse, AxiosError } from 'axios';
import { ProxyService } from '../src/proxy/proxy.service';
import { ConfigService } from '../src/config/config.service';
import { PolicyService } from '../src/policy/policy.service';
import { UpstreamUnavailableException } from '../src/common/errors';

describe('ProxyService', () => {
  let service: ProxyService;
  let httpService: HttpService;
  let policyService: PolicyService;

  const mockPolicy = {
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
        ProxyService,
        {
          provide: HttpService,
          useValue: {
            request: jest.fn(),
          },
        },
        {
          provide: ConfigService,
          useValue: {},
        },
        {
          provide: PolicyService,
          useValue: {
            loader: {
              load: jest.fn().mockResolvedValue(mockPolicy),
            },
          },
        },
      ],
    }).compile();

    service = module.get<ProxyService>(ProxyService);
    httpService = module.get<HttpService>(HttpService);
    policyService = module.get<PolicyService>(PolicyService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  it('should proxy request successfully', async () => {
    const mockResponse: AxiosResponse = {
      data: { ok: true },
      status: 200,
      statusText: 'OK',
      headers: {},
      config: {} as any,
    };

    (httpService.request as jest.Mock).mockReturnValue(of(mockResponse));

    const req = {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      query: {},
      body: { test: 'data' },
    } as any;

    const res = {
      status: jest.fn().mockReturnThis(),
      setHeader: jest.fn(),
      json: jest.fn(),
    } as any;

    const context = {
      tenantId: 'tenant1',
      userId: 'user1',
      scopes: ['scope1'],
      requestId: 'req123',
    };

    await service.proxy(req, res, '/v1/orchestrations/sales-email/run', context);

    expect(httpService.request).toHaveBeenCalled();
    expect(res.status).toHaveBeenCalledWith(200);
    expect(res.json).toHaveBeenCalledWith({ ok: true });
  });

  it('should handle upstream errors', async () => {
    const axiosError = {
      response: {
        status: 500,
        data: { ok: false, error_code: 'INTERNAL_ERROR' },
      },
      code: 'ECONNREFUSED',
    } as AxiosError;

    (httpService.request as jest.Mock).mockReturnValue(throwError(() => axiosError));

    const req = {
      method: 'POST',
      headers: {},
      query: {},
      body: {},
    } as any;

    const res = {
      status: jest.fn().mockReturnThis(),
      json: jest.fn(),
    } as any;

    const context = {
      tenantId: 'tenant1',
      userId: 'user1',
      scopes: [],
      requestId: 'req123',
    };

    await service.proxy(req, res, '/v1/orchestrations/sales-email/run', context);

    expect(res.status).toHaveBeenCalledWith(500);
    expect(res.json).toHaveBeenCalledWith({
      ok: false,
      error_code: 'INTERNAL_ERROR',
    });
  });
});

