import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request, Response } from 'express';
import { logRequest, logError } from '../logger';
import { MCSRequestContext } from '../types';
import { HEADER_REQUEST_ID } from '../constants';
import { redactHeaders } from '../utils/headers';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest<Request>();
    const response = context.switchToHttp().getResponse<Response>();
    const startTime = Date.now();

    const requestId =
      (request.headers[HEADER_REQUEST_ID] as string) || 'unknown';
    const mcsContext = (request as any).mcs as MCSRequestContext;

    // Log request (redacted)
    const redactedHeaders = redactHeaders(request.headers);
    // Don't log body to avoid sensitive data

    return next.handle().pipe(
      tap({
        next: () => {
          const latencyMs = Date.now() - startTime;
          logRequest(
            requestId,
            mcsContext?.tenantId,
            mcsContext?.userId,
            request.method,
            request.path,
            response.statusCode,
            latencyMs,
          );
        },
        error: (error) => {
          const latencyMs = Date.now() - startTime;
          logError(requestId, error, {
            method: request.method,
            path: request.path,
            status: response.statusCode,
            latency_ms: latencyMs,
            tenant_id: mcsContext?.tenantId,
            user_id: mcsContext?.userId,
          });
        },
      }),
    );
  }
}

