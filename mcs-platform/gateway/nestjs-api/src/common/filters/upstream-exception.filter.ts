import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { UpstreamUnavailableException } from '../errors';
import { HEADER_REQUEST_ID } from '../constants';

@Catch(UpstreamUnavailableException)
export class UpstreamExceptionFilter implements ExceptionFilter {
  catch(exception: UpstreamUnavailableException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const requestId =
      (request.headers[HEADER_REQUEST_ID] as string) ||
      (request as any).mcs?.requestId ||
      'unknown';

    const errorResponse: any = {
      ok: false,
      error_code: exception.errorCode,
      reason: exception.message,
      request_id: requestId,
    };

    if (exception.upstreamStatus) {
      errorResponse.upstream_status = exception.upstreamStatus;
    }

    if (exception.upstreamErrorCode) {
      errorResponse.upstream_error_code = exception.upstreamErrorCode;
    }

    response.status(exception.getStatus()).json(errorResponse);
  }
}

