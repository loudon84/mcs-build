import {
  Injectable,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import { Request } from 'express';
import { MCSRequestContext } from '../common/types';
import { InvalidTokenException } from '../common/errors';
import { getOrGenerateRequestId } from '../common/utils/request-id';
import { HEADER_REQUEST_ID } from '../common/constants';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  canActivate(context: ExecutionContext) {
    return super.canActivate(context);
  }

  handleRequest(err: any, user: any, info: any, context: ExecutionContext) {
    const request = context.switchToHttp().getRequest<Request>();

    if (err || !user) {
      if (info?.name === 'TokenExpiredError') {
        throw new InvalidTokenException('Token expired');
      }
      if (info?.name === 'JsonWebTokenError') {
        throw new InvalidTokenException('Invalid token');
      }
      throw new UnauthorizedException('Unauthorized');
    }

    // Attach MCS context to request
    const requestId = getOrGenerateRequestId(
      request.headers[HEADER_REQUEST_ID] as string,
    );

    const mcsContext: MCSRequestContext = {
      tenantId: user.tenant_id,
      userId: user.sub,
      scopes: user.scopes || [],
      requestId,
    };

    // Attach to request object
    (request as any).mcs = mcsContext;

    return user;
  }
}

// Export as default for convenience
export default JwtAuthGuard;

