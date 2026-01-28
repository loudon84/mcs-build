import { Injectable } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { Request, Response } from 'express';
import { firstValueFrom, retry, catchError } from 'rxjs';
import { AxiosError, AxiosRequestConfig } from 'axios';
import { ConfigService } from '../config/config.service';
import { PolicyService } from '../policy/policy.service';
import { MCSRequestContext } from '../common/types';
import { UpstreamUnavailableException } from '../common/errors';

@Injectable()
export class ProxyService {
  constructor(
    private httpService: HttpService,
    private configService: ConfigService,
    private policyService: PolicyService,
  ) {}

  async proxy(
    req: Request,
    res: Response,
    upstreamPath: string,
    context: MCSRequestContext,
    body?: any,
  ): Promise<void> {
    const policy = await this.policyService['loader'].load();
    const baseUrl = policy.routing.orchestrator_base_url;
    const timeout = policy.routing.timeout_ms;
    const retryConfig = policy.routing.retry;

    const url = `${baseUrl}${upstreamPath}`;
    const upstreamHeaders = (req as any).upstreamHeaders || {};

    // Build request config
    const requestConfig: AxiosRequestConfig = {
      method: req.method as any,
      url,
      headers: {
        ...upstreamHeaders,
        'Content-Type': req.headers['content-type'] || 'application/json',
      },
      params: req.query,
      data: body || req.body,
      timeout,
      validateStatus: () => true, // Don't throw on any status
    };

    try {
      let request$ = this.httpService.request(requestConfig);

      // Add retry logic if enabled
      if (retryConfig?.enabled) {
        const retryableStatuses = [502, 503, 504];
        request$ = request$.pipe(
          retry({
            count: retryConfig.max_retries,
            delay: (error: AxiosError, retryCount: number) => {
              if (
                error.response &&
                retryableStatuses.includes(error.response.status)
              ) {
                return 1000 * retryCount; // Exponential backoff
              }
              throw error;
            },
          }),
        );
      }

      const response = await firstValueFrom(request$);

      // Forward status and headers
      res.status(response.status);

      // Forward response headers (except sensitive ones)
      Object.keys(response.headers).forEach((key) => {
        const value = response.headers[key];
        if (value && !key.toLowerCase().startsWith('x-')) {
          res.setHeader(key, value);
        }
      });

      // Forward response body
      res.json(response.data);
    } catch (error) {
      if (error instanceof AxiosError) {
        if (error.response) {
          // Upstream returned an error
          res.status(error.response.status);
          res.json(error.response.data);
        } else if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
          // Timeout
          throw new UpstreamUnavailableException(
            'Upstream request timeout',
            504,
          );
        } else {
          // Connection error
          throw new UpstreamUnavailableException(
            'Upstream service unavailable',
            503,
          );
        }
      } else {
        throw error;
      }
    }
  }
}

