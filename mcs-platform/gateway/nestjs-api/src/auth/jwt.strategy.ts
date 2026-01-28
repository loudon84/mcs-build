import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '../config/config.service';
import { InvalidTokenException, UnauthorizedException as MCSUnauthorizedException } from '../common/errors';
import { JWTPayload } from '../common/types';
import * as jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  private jwksClient: ReturnType<typeof jwksClient> | null = null;

  constructor(private configService: ConfigService) {
    const jwksUrl = configService.jwtJwksUrl;
    const publicKey = configService.jwtPublicKey;

    if (!jwksUrl && !publicKey) {
      throw new Error('Either JWT_JWKS_URL or JWT_PUBLIC_KEY must be configured');
    }

    // Initialize JWKS client if URL is provided
    if (jwksUrl) {
      this.jwksClient = jwksClient({
        jwksUri: jwksUrl,
        cache: true,
        cacheMaxAge: 86400000, // 24 hours
      });
    }

    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKeyProvider: async (request, rawJwtToken, done) => {
        try {
          if (publicKey) {
            // Use static public key
            done(null, publicKey);
          } else if (this.jwksClient) {
            // Get key from JWKS
            const decoded = jwt.decode(rawJwtToken, { complete: true });
            if (!decoded || typeof decoded === 'string' || !decoded.header.kid) {
              return done(new Error('Invalid token header'), null);
            }

            const key = await this.jwksClient.getSigningKey(decoded.header.kid);
            const signingKey = key.getPublicKey();
            done(null, signingKey);
          } else {
            done(new Error('No JWT verification method configured'), null);
          }
        } catch (error) {
          done(error, null);
        }
      },
    });
  }

  async validate(payload: any): Promise<JWTPayload> {
    // Extract required fields
    const userId = payload.sub;
    const tenantId = payload.tenant_id || payload.tenantId;

    if (!userId) {
      throw new InvalidTokenException('Missing user_id (sub) in token');
    }

    if (!tenantId) {
      throw new InvalidTokenException('Missing tenant_id in token');
    }

    // Extract scopes
    let scopes: string[] = [];
    if (payload.scopes && Array.isArray(payload.scopes)) {
      scopes = payload.scopes;
    } else if (payload.scope && typeof payload.scope === 'string') {
      scopes = payload.scope.split(' ').filter((s: string) => s.length > 0);
    }

    return {
      sub: userId,
      tenant_id: tenantId,
      scopes,
      ...payload,
    };
  }
}

