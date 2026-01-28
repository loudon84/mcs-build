import { Module } from '@nestjs/common';
import { OrchestrationsController } from './orchestrations.controller';
import { ProxyModule } from '../../proxy/proxy.module';
import { PolicyModule } from '../../policy/policy.module';
import { RatelimitModule } from '../../ratelimit/ratelimit.module';

@Module({
  imports: [ProxyModule, PolicyModule, RatelimitModule],
  controllers: [OrchestrationsController],
})
export class OrchestrationsModule {}

