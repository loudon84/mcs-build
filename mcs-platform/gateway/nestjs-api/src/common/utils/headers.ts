import { HEADER_REQUEST_ID, HEADER_TENANT_ID, HEADER_USER_ID, HEADER_SCOPES, HEADER_GRAPH_NAME, HEADER_GRAPH_VERSION, HEADER_CLIENT_APP, HEADER_TRACEPARENT } from '../constants';
import { MCSRequestContext } from '../types';

/**
 * Redact sensitive headers for logging
 */
export function redactHeaders(headers: Record<string, string | string[] | undefined>): Record<string, string | string[]> {
  const redacted = { ...headers };
  if (redacted['authorization']) {
    redacted['authorization'] = '***REDACTED***';
  }
  return redacted;
}

/**
 * Build headers for upstream request
 */
export function buildUpstreamHeaders(context: MCSRequestContext, additionalHeaders?: Record<string, string>): Record<string, string> {
  const headers: Record<string, string> = {
    [HEADER_REQUEST_ID]: context.requestId,
    [HEADER_TENANT_ID]: context.tenantId,
    [HEADER_USER_ID]: context.userId,
    [HEADER_SCOPES]: context.scopes.join(','),
  };

  if (context.graphName) {
    headers[HEADER_GRAPH_NAME] = context.graphName;
  }

  if (context.graphVersion) {
    headers[HEADER_GRAPH_VERSION] = context.graphVersion;
  }

  if (additionalHeaders) {
    Object.assign(headers, additionalHeaders);
  }

  // Preserve traceparent if present
  if (additionalHeaders?.[HEADER_TRACEPARENT]) {
    headers[HEADER_TRACEPARENT] = additionalHeaders[HEADER_TRACEPARENT];
  }

  return headers;
}

