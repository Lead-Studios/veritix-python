import { Controller, Get, Post, Put, Delete, Body, Param, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { AdminSettingsService } from './admin-settings.service';
import { CreateAdminSettingsDto } from './dtos/create-admin-settings.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@ApiTags('Admin Settings')
@Controller('admin/settings')
export class AdminSettingsController {
  constructor(private readonly service: AdminSettingsService) {}

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create admin settings' })
  async create(@Param('adminId') adminId: string, @Body() dto: CreateAdminSettingsDto) {
    return this.service.create(adminId, dto);
  }

  @Get('/:adminId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get admin settings' })
  async findByAdmin(@Param('adminId') adminId: string) {
    return this.service.findByAdmin(adminId);
  }

  @Put('/:adminId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update admin settings' })
  async update(@Param('adminId') adminId: string, @Body() dto: CreateAdminSettingsDto) {
    return this.service.update(adminId, dto);
  }

  @Get()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get all admin settings' })
  async getAll(@Query() pagination: PaginationDto) {
    const [data, total] = await this.service.getAll(pagination);
    return { data, total, page: pagination.page, limit: pagination.limit };
  }

  @Delete('/:adminId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete admin settings' })
  async delete(@Param('adminId') adminId: string) {
    await this.service.delete(adminId);
    return { message: 'Admin settings deleted' };
  }
}
