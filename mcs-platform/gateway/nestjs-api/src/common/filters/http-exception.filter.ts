import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { ERROR_CODES, HTTP_STATUS_MAP, HEADER_REQUEST_ID } from '../constants';
import { MCSException } from '../errors';

@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
    const status = exception.getStatus();

    // Get request ID
    const requestId =
      (request.headers[HEADER_REQUEST_ID] as string) ||
      (request as any).mcs?.requestId ||
      'unknown';

    // If it's already an MCSException, use its format
    if (exception instanceof MCSException) {
      const errorResponse = exception.getResponse() as any;
      response.status(status).json({
        ...errorResponse,
        request_id: requestId,
      });
      return;
    }

    // Map HTTP status to error code
    const errorCode =
      HTTP_STATUS_MAP[status as keyof typeof HTTP_STATUS_MAP] ||
      ERROR_CODES.INTERNAL_ERROR;

    const errorResponse = {
      ok: false,
      error_code: errorCode,
      reason: exception.message || 'An error occurred',
      request_id: requestId,
    };

    response.status(status).json(errorResponse);
  }
}

