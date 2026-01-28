import { Controller, Get } from '@nestjs/common';

@Controller('healthz')
export class HealthController {
  @Get()
  healthz() {
    return {
      status: 'ok',
      service: 'mcs-gateway',
      timestamp: new Date().toISOString(),
    };
  }
}

