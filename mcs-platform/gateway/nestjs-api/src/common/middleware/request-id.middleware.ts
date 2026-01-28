import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { getOrGenerateRequestId } from '../utils/request-id';
import { HEADER_REQUEST_ID } from '../constants';

@Injectable()
export class RequestIdMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const existingRequestId = req.headers[HEADER_REQUEST_ID] as string | undefined;
    const requestId = getOrGenerateRequestId(existingRequestId);

    // Attach to request
    req.headers[HEADER_REQUEST_ID] = requestId;

    // Set response header
    res.setHeader(HEADER_REQUEST_ID, requestId);

    next();
  }
}

