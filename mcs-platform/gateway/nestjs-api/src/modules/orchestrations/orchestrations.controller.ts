import {
  Controller,
  Post,
  Param,
  Body,
  Req,
  Res,
  UseGuards,
  Headers,
} from '@nestjs/common';
import { Request, Response } from 'express';
import { JwtAuthGuard } from '../../auth/auth.guard';
import { PolicyGuard } from '../../policy/policy.guard';
import { RatelimitGuard } from '../../ratelimit/ratelimit.guard';
import { ProxyService } from '../../proxy/proxy.service';
import { MCSRequestContext } from '../../common/types';
import { HEADER_GRAPH_VERSION } from '../../common/constants';

@Controller('orchestrations')
@UseGuards(JwtAuthGuard, PolicyGuard, RatelimitGuard)
export class OrchestrationsController {
  constructor(private readonly proxyService: ProxyService) {}

  @Post(':graph/run')
  async run(
    @Param('graph') graph: string,
    @Body() body: any,
    @Headers(HEADER_GRAPH_VERSION) version: string | undefined,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    context.graphName = graph;
    if (version) {
      context.graphVersion = version;
    }
    return this.proxyService.proxy(
      req,
      res,
      `/v1/orchestrations/${graph}/run`,
      context,
      body,
    );
  }

  @Post(':graph/replay')
  async replay(
    @Param('graph') graph: string,
    @Body() body: any,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    context.graphName = graph;
    return this.proxyService.proxy(
      req,
      res,
      `/v1/orchestrations/${graph}/replay`,
      context,
      body,
    );
  }

  @Post(':graph/manual-review/submit')
  async submitManualReview(
    @Param('graph') graph: string,
    @Body() body: any,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    context.graphName = graph;
    return this.proxyService.proxy(
      req,
      res,
      `/v1/orchestrations/${graph}/manual-review/submit`,
      context,
      body,
    );
  }
}

