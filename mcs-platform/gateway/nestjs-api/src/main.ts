import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { AppModule } from './app.module';
import { HttpExceptionFilter } from './common/filters/http-exception.filter';
import { UpstreamExceptionFilter } from './common/filters/upstream-exception.filter';
import { RequestIdMiddleware } from './common/middleware/request-id.middleware';
import { MCSContextInterceptor } from './common/interceptors/mcs-context.interceptor';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Global validation pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: false, // Allow unknown properties for opaque payloads
      transform: false, // Don't transform payloads - keep them opaque
    }),
  );

  // Global exception filters
  app.useGlobalFilters(
    new HttpExceptionFilter(),
    new UpstreamExceptionFilter(),
  );

  // Global middleware
  app.use(RequestIdMiddleware);

  // Global interceptors
  app.useGlobalInterceptors(
    new MCSContextInterceptor(),
    new LoggingInterceptor(),
  );

  // Global prefix
  app.setGlobalPrefix('api/mcs/v1');

  const port = process.env.PORT || 3000;
  await app.listen(port);
  console.log(`MCS Gateway listening on port ${port}`);
}

bootstrap();

