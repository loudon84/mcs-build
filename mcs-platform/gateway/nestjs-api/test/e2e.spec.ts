import { Test, TestingModule } from '@nestjs/testing';
import { INestApplication } from '@nestjs/common';
import * as request from 'supertest';
import { AppModule } from '../src/app.module';

describe('E2E Tests', () => {
  let app: INestApplication;

  beforeEach(async () => {
    const moduleFixture: TestingModule = await Test.createTestingModule({
      imports: [AppModule],
    }).compile();

    app = moduleFixture.createNestApplication();
    await app.init();
  });

  afterEach(async () => {
    await app.close();
  });

  it('/healthz (GET) should return health status', () => {
    return request(app.getHttpServer())
      .get('/api/mcs/v1/healthz')
      .expect(200)
      .expect((res) => {
        expect(res.body.status).toBe('ok');
        expect(res.body.service).toBe('mcs-gateway');
      });
  });

  it('/orchestrations/:graph/run (POST) should require authentication', () => {
    return request(app.getHttpServer())
      .post('/api/mcs/v1/orchestrations/sales-email/run')
      .send({})
      .expect(401);
  });
});

