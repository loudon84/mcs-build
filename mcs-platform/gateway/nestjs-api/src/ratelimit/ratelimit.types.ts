export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number; // Unix timestamp
  retryAfter?: number; // Seconds until reset
}

export interface RateLimitStore {
  check(key: string, limit: number, windowMs: number): Promise<RateLimitResult>;
  increment(key: string, windowMs: number): Promise<number>;
}

