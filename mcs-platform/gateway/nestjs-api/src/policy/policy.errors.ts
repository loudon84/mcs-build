import {
  PermissionDeniedException,
  VersionNotAllowedException,
  InsufficientScopeException,
} from '../common/errors';

export class GraphNotAllowedError extends PermissionDeniedException {
  constructor(graphName: string, tenantId: string) {
    super(`Graph '${graphName}' is not allowed for tenant '${tenantId}'`);
  }
}

export class GraphVersionNotAllowedError extends VersionNotAllowedException {
  constructor(graphName: string, version: string, tenantId: string) {
    super(
      `Version '${version}' of graph '${graphName}' is not allowed for tenant '${tenantId}'`,
    );
  }
}

export class InsufficientScopesError extends InsufficientScopeException {
  constructor(required: string[], provided: string[]) {
    super(
      `Required scopes: ${required.join(', ')}, provided: ${provided.join(', ')}`,
    );
  }
}

