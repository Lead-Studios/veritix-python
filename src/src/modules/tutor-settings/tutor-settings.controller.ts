import { Controller, Get, Post, Put, Delete, Body, Param, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { TutorSettingsService } from './tutor-settings.service';
import { CreateTutorSettingsDto } from './dtos/create-tutor-settings.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@ApiTags('Tutor Settings')
@Controller('tutor/settings')
export class TutorSettingsController {
  constructor(private readonly service: TutorSettingsService) {}

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('tutor')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create tutor settings' })
  async create(@Param('tutorId') tutorId: string, @Body() dto: CreateTutorSettingsDto) {
    return this.service.create(tutorId, dto);
  }

  @Get('/:tutorId')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get tutor settings' })
  async findByTutor(@Param('tutorId') tutorId: string) {
    return this.service.findByTutor(tutorId);
  }

  @Put('/:tutorId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('tutor')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update tutor settings' })
  async update(@Param('tutorId') tutorId: string, @Body() dto: CreateTutorSettingsDto) {
    return this.service.update(tutorId, dto);
  }

  @Get()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get all tutor settings' })
  async getAll(@Query() pagination: PaginationDto) {
    const [data, total] = await this.service.getAll(pagination);
    return { data, total, page: pagination.page, limit: pagination.limit };
  }

  @Delete('/:tutorId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('tutor', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete tutor settings' })
  async delete(@Param('tutorId') tutorId: string) {
    await this.service.delete(tutorId);
    return { message: 'Tutor settings deleted' };
  }
}
