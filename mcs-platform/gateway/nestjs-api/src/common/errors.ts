import { HttpException, HttpStatus } from '@nestjs/common';
import { ERROR_CODES } from './constants';

export class MCSException extends HttpException {
  constructor(
    public readonly errorCode: string,
    message: string,
    statusCode: HttpStatus = HttpStatus.INTERNAL_SERVER_ERROR,
  ) {
    super(
      {
        ok: false,
        error_code: errorCode,
        reason: message,
      },
      statusCode,
    );
  }
}

export class UnauthorizedException extends MCSException {
  constructor(message = 'Unauthorized') {
    super(ERROR_CODES.UNAUTHORIZED, message, HttpStatus.UNAUTHORIZED);
  }
}

export class InvalidTokenException extends MCSException {
  constructor(message = 'Invalid token') {
    super(ERROR_CODES.INVALID_TOKEN, message, HttpStatus.UNAUTHORIZED);
  }
}

export class PermissionDeniedException extends MCSException {
  constructor(message = 'Permission denied') {
    super(ERROR_CODES.PERMISSION_DENIED, message, HttpStatus.FORBIDDEN);
  }
}

export class VersionNotAllowedException extends MCSException {
  constructor(message = 'Version not allowed') {
    super(ERROR_CODES.VERSION_NOT_ALLOWED, message, HttpStatus.FORBIDDEN);
  }
}

export class InsufficientScopeException extends MCSException {
  constructor(message = 'Insufficient scope') {
    super(ERROR_CODES.INSUFFICIENT_SCOPE, message, HttpStatus.FORBIDDEN);
  }
}

export class RateLimitedException extends MCSException {
  constructor(message = 'Rate limit exceeded', retryAfter?: number) {
    super(ERROR_CODES.RATE_LIMITED, message, HttpStatus.TOO_MANY_REQUESTS);
    if (retryAfter) {
      this.options = {
        ...this.options,
        headers: {
          'Retry-After': retryAfter.toString(),
        },
      };
    }
  }
}

export class NotFoundException extends MCSException {
  constructor(message = 'Not found') {
    super(ERROR_CODES.NOT_FOUND, message, HttpStatus.NOT_FOUND);
  }
}

export class UpstreamUnavailableException extends MCSException {
  constructor(
    message = 'Upstream service unavailable',
    public readonly upstreamStatus?: number,
    public readonly upstreamErrorCode?: string,
  ) {
    super(ERROR_CODES.UPSTREAM_UNAVAILABLE, message, HttpStatus.BAD_GATEWAY);
  }
}

