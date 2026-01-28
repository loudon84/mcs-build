import { Module } from '@nestjs/common';
import { ConfigModule } from './config/config.module';
import { HealthModule } from './modules/health/health.module';
import { PlatformModule } from './modules/platform/platform.module';
import { OrchestrationsModule } from './modules/orchestrations/orchestrations.module';
import { AuthModule } from './auth/auth.module';
import { PolicyModule } from './policy/policy.module';
import { RatelimitModule } from './ratelimit/ratelimit.module';
import { ProxyModule } from './proxy/proxy.module';

@Module({
  imports: [
    ConfigModule,
    AuthModule,
    PolicyModule,
    RatelimitModule,
    ProxyModule,
    HealthModule,
    PlatformModule,
    OrchestrationsModule,
  ],
})
export class AppModule {}

