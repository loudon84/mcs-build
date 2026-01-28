import { Module } from '@nestjs/common';
import { RateLimitService } from './ratelimit.service';
import { RatelimitGuard } from './ratelimit.guard';
import { ConfigModule } from '../config/config.module';
import { PolicyModule } from '../policy/policy.module';

@Module({
  imports: [ConfigModule, PolicyModule],
  providers: [RateLimitService, RatelimitGuard],
  exports: [RatelimitGuard],
})
export class RatelimitModule {}

