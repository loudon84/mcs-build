import { Module } from '@nestjs/common';
import { PlatformController } from './platform.controller';
import { ProxyModule } from '../../proxy/proxy.module';

@Module({
  imports: [ProxyModule],
  controllers: [PlatformController],
})
export class PlatformModule {}

