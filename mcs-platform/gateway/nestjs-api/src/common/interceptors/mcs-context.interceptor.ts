import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { Request } from 'express';
import { MCSRequestContext } from '../types';
import { buildUpstreamHeaders } from '../utils/headers';
import { HEADER_CLIENT_APP } from '../constants';

@Injectable()
export class MCSContextInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest<Request>();
    const mcsContext = (request as any).mcs as MCSRequestContext;

    if (mcsContext) {
      // Build headers for upstream
      const upstreamHeaders = buildUpstreamHeaders(mcsContext, {
        // Preserve traceparent if present
        ...(request.headers['traceparent'] && {
          traceparent: request.headers['traceparent'] as string,
        }),
        // Add client app if present
        ...(request.headers[HEADER_CLIENT_APP] && {
          [HEADER_CLIENT_APP]: request.headers[HEADER_CLIENT_APP] as string,
        }),
      });

      // Attach to request for proxy service to use
      (request as any).upstreamHeaders = upstreamHeaders;
    }

    return next.handle();
  }
}

