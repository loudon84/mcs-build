import { Controller, Get, Param, Req, Res, UseGuards } from '@nestjs/common';
import { Request, Response } from 'express';
import { JwtAuthGuard } from '../../auth/auth.guard';
import { ProxyService } from '../../proxy/proxy.service';
import { MCSRequestContext } from '../../common/types';

@Controller('platform')
@UseGuards(JwtAuthGuard)
export class PlatformController {
  constructor(private readonly proxyService: ProxyService) {}

  @Get('graphs')
  async getGraphs(@Req() req: Request, @Res() res: Response) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(req, res, '/v1/platform/graphs', context);
  }

  @Get('graphs/:name')
  async getGraph(
    @Param('name') name: string,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(req, res, `/v1/platform/graphs/${name}`, context);
  }

  @Get('graphs/:name/:version/schema')
  async getGraphSchema(
    @Param('name') name: string,
    @Param('version') version: string,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(
      req,
      res,
      `/v1/platform/graphs/${name}/${version}/schema`,
      context,
    );
  }

  @Get('tools')
  async getTools(@Req() req: Request, @Res() res: Response) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(req, res, '/v1/platform/tools', context);
  }

  @Get('tools/:name')
  async getTool(
    @Param('name') name: string,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(req, res, `/v1/platform/tools/${name}`, context);
  }

  @Get('tools/:name/:version/schema')
  async getToolSchema(
    @Param('name') name: string,
    @Param('version') version: string,
    @Req() req: Request,
    @Res() res: Response,
  ) {
    const context = req.mcs as MCSRequestContext;
    return this.proxyService.proxy(
      req,
      res,
      `/v1/platform/tools/${name}/${version}/schema`,
      context,
    );
  }
}

