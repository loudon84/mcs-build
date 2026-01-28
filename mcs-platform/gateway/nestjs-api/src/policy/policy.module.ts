import { Module } from '@nestjs/common';
import { PolicyService } from './policy.service';
import { YamlPolicyLoader } from './policy.loader';
import { ConfigModule } from '../config/config.module';

@Module({
  imports: [ConfigModule],
  providers: [
    YamlPolicyLoader,
    {
      provide: 'PolicyLoader',
      useExisting: YamlPolicyLoader,
    },
    PolicyService,
  ],
  exports: [PolicyService],
})
export class PolicyModule {}

