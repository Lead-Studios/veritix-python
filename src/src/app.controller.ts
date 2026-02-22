import { Controller, Get } from '@nestjs/common';
import { AppService } from './app.service';

@Controller()
export class AppController {
  constructor(private readonly appService: AppService) {}

  @Get()
  getHello(): object {
    return this.appService.getHello();
  }

  @Get('health')
  health(): object {
    return { status: 'ok', timestamp: new Date().toISOString() };
  }

  @Get('api/modules')
  getModules(): object {
    return this.appService.getAllModules();
  }
}
