import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { Request } from 'express';
import { PolicyService } from './policy.service';
import { MCSRequestContext } from '../common/types';
import { HEADER_GRAPH_VERSION } from '../common/constants';

@Injectable()
export class PolicyGuard implements CanActivate {
  constructor(private policyService: PolicyService) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const request = context.switchToHttp().getRequest<Request>();
    const mcsContext = (request as any).mcs as MCSRequestContext;

    if (!mcsContext?.graphName) {
      // No graph name in path, skip policy check
      return true;
    }

    const graphName = mcsContext.graphName;
    const tenantId = mcsContext.tenantId;
    const requestedVersion = request.headers[HEADER_GRAPH_VERSION] as string | undefined;

    // Resolve version
    const resolvedVersion = this.policyService.resolveGraphVersion(
      tenantId,
      graphName,
      requestedVersion,
    );

    // Assert graph is allowed
    this.policyService.assertGraphAllowed(tenantId, graphName, resolvedVersion);

    // Get graph config for scope check
    const graphConfig = this.policyService.getGraphConfig(tenantId, graphName);
    if (graphConfig) {
      // Assert scopes
      this.policyService.assertScopes(
        graphConfig.required_scopes,
        mcsContext.scopes,
      );
    }

    // Update context with resolved version
    mcsContext.graphVersion = resolvedVersion;

    return true;
  }
}

