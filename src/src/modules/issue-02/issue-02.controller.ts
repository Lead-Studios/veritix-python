import { Controller, Get, Post, Body, Param, Put, Delete, Query } from '@nestjs/common';
import { Issue02Service } from './issue-02.service';
import { CreateIssue02Dto, UpdateIssue02Dto } from './issue-02.dto';
import { Issue02Product } from './issue-02.entity';

@Controller('api/issue-02/products')
export class Issue02Controller {
  constructor(private readonly service: Issue02Service) {}

  @Post()
  create(@Body() dto: CreateIssue02Dto): Promise<Issue02Product> {
    return this.service.create(dto);
  }

  @Get()
  findAll(@Query('category') category?: string): Promise<Issue02Product[]> {
    if (category) {
      return this.service.findByCategory(category);
    }
    return this.service.findAll();
  }

  @Get(':id')
  findOne(@Param('id') id: string): Promise<Issue02Product> {
    return this.service.findOne(id);
  }

  @Put(':id')
  update(
    @Param('id') id: string,
    @Body() dto: UpdateIssue02Dto,
  ): Promise<Issue02Product> {
    return this.service.update(id, dto);
  }

  @Delete(':id')
  remove(@Param('id') id: string): Promise<void> {
    return this.service.remove(id);
  }
}
