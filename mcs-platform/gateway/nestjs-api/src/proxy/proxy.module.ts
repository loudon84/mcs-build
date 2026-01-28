import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { ProxyService } from './proxy.service';
import { ConfigModule } from '../config/config.module';
import { PolicyModule } from '../policy/policy.module';

@Module({
  imports: [
    HttpModule.register({
      timeout: 30000,
      maxRedirects: 5,
    }),
    ConfigModule,
    PolicyModule,
  ],
  providers: [ProxyService],
  exports: [ProxyService],
})
export class ProxyModule {}

