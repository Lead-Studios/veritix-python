import { Controller, Get, Post, Body, Param, Put, Delete } from '@nestjs/common';
import { Issue01Service } from './issue-01.service';
import { CreateIssue01Dto, UpdateIssue01Dto } from './issue-01.dto';
import { Issue01UserProfile } from './issue-01.entity';

@Controller('api/issue-01/profiles')
export class Issue01Controller {
  constructor(private readonly service: Issue01Service) {}

  @Post()
  create(@Body() dto: CreateIssue01Dto): Promise<Issue01UserProfile> {
    return this.service.create(dto);
  }

  @Get()
  findAll(): Promise<Issue01UserProfile[]> {
    return this.service.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string): Promise<Issue01UserProfile> {
    return this.service.findOne(id);
  }

  @Put(':id')
  update(
    @Param('id') id: string,
    @Body() dto: UpdateIssue01Dto,
  ): Promise<Issue01UserProfile> {
    return this.service.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string): Promise<void> {
    return this.service.remove(id);
  }
}
