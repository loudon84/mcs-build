import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '../config/config.service';
import { RateLimitStore, RateLimitResult } from './ratelimit.types';
import { RateLimitConfig } from '../common/types';
import Redis from 'ioredis';

@Injectable()
export class RateLimitService implements RateLimitStore {
  private redis: Redis | null = null;
  private memoryStore: Map<string, { count: number; resetAt: number }> = new Map();

  constructor(private configService: ConfigService) {}

  async onModuleInit() {
    const redisUrl = this.configService.rateLimitRedisUrl;
    if (redisUrl) {
      try {
        this.redis = new Redis(redisUrl, {
          retryStrategy: (times) => {
            const delay = Math.min(times * 50, 2000);
            return delay;
          },
        });
        await this.redis.ping();
        console.log('Rate limiting using Redis');
      } catch (error) {
        console.warn('Failed to connect to Redis, falling back to memory store:', error);
        this.redis = null;
      }
    } else {
      console.log('Rate limiting using in-memory store');
    }
  }

  async onModuleDestroy() {
    if (this.redis) {
      await this.redis.quit();
    }
  }

  async check(
    key: string,
    limit: number,
    windowMs: number,
  ): Promise<RateLimitResult> {
    if (this.redis) {
      return this.checkRedis(key, limit, windowMs);
    } else {
      return this.checkMemory(key, limit, windowMs);
    }
  }

  private async checkRedis(
    key: string,
    limit: number,
    windowMs: number,
  ): Promise<RateLimitResult> {
    const now = Date.now();
    const windowKey = `ratelimit:${key}:${Math.floor(now / windowMs)}`;
    const resetAt = (Math.floor(now / windowMs) + 1) * windowMs;

    try {
      const count = await this.redis.incr(windowKey);
      if (count === 1) {
        await this.redis.pexpire(windowKey, windowMs);
      }

      const allowed = count <= limit;
      const remaining = Math.max(0, limit - count);
      const retryAfter = allowed ? undefined : Math.ceil((resetAt - now) / 1000);

      return {
        allowed,
        remaining,
        resetAt,
        retryAfter,
      };
    } catch (error) {
      // Fallback to memory on Redis error
      console.warn('Redis error, falling back to memory:', error);
      return this.checkMemory(key, limit, windowMs);
    }
  }

  private async checkMemory(
    key: string,
    limit: number,
    windowMs: number,
  ): Promise<RateLimitResult> {
    const now = Date.now();
    const entry = this.memoryStore.get(key);

    if (!entry || entry.resetAt <= now) {
      // New window or expired
      this.memoryStore.set(key, {
        count: 1,
        resetAt: now + windowMs,
      });

      return {
        allowed: true,
        remaining: limit - 1,
        resetAt: now + windowMs,
      };
    }

    entry.count += 1;
    const allowed = entry.count <= limit;
    const remaining = Math.max(0, limit - entry.count);
    const retryAfter = allowed ? undefined : Math.ceil((entry.resetAt - now) / 1000);

    return {
      allowed,
      remaining,
      resetAt: entry.resetAt,
      retryAfter,
    };
  }

  async increment(key: string, windowMs: number): Promise<number> {
    if (this.redis) {
      const now = Date.now();
      const windowKey = `ratelimit:${key}:${Math.floor(now / windowMs)}`;
      const count = await this.redis.incr(windowKey);
      if (count === 1) {
        await this.redis.pexpire(windowKey, windowMs);
      }
      return count;
    } else {
      const entry = this.memoryStore.get(key);
      if (!entry || entry.resetAt <= Date.now()) {
        this.memoryStore.set(key, {
          count: 1,
          resetAt: Date.now() + windowMs,
        });
        return 1;
      }
      entry.count += 1;
      return entry.count;
    }
  }
}

