import { JWTPayload } from '../common/types';

export interface JWTValidationOptions {
  jwksUrl?: string;
  publicKey?: string;
  issuer?: string;
  audience?: string;
}

export interface JWTValidationResult {
  payload: JWTPayload;
  isValid: boolean;
  error?: string;
}

