import { Logger } from '@nestjs/common';

export const logger = new Logger('MCSGateway');

export function logRequest(
  requestId: string,
  tenantId: string | undefined,
  userId: string | undefined,
  method: string,
  path: string,
  status: number,
  latencyMs: number,
) {
  logger.log({
    request_id: requestId,
    tenant_id: tenantId,
    user_id: userId,
    method,
    path,
    status,
    latency_ms: latencyMs,
  });
}

export function logError(
  requestId: string,
  error: Error,
  context?: Record<string, any>,
) {
  logger.error(
    {
      request_id: requestId,
      error: error.message,
      stack: error.stack,
      ...context,
    },
    error.stack,
  );
}

