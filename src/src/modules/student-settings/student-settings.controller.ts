import { Controller, Get, Post, Put, Delete, Body, Param, UseGuards, Query } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { StudentSettingsService } from './student-settings.service';
import { CreateStudentSettingsDto } from './dtos/create-student-settings.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';
import { RolesGuard } from '../../common/guards/roles.guard';
import { Roles } from '../../common/decorators/roles.decorator';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@ApiTags('Student Settings')
@Controller('student/settings')
export class StudentSettingsController {
  constructor(private readonly service: StudentSettingsService) {}

  @Post()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('student')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create student settings' })
  async create(@Param('studentId') studentId: string, @Body() dto: CreateStudentSettingsDto) {
    return this.service.create(studentId, dto);
  }

  @Get('/:studentId')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get student settings' })
  async findByStudent(@Param('studentId') studentId: string) {
    return this.service.findByStudent(studentId);
  }

  @Put('/:studentId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('student')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update student settings' })
  async update(@Param('studentId') studentId: string, @Body() dto: CreateStudentSettingsDto) {
    return this.service.update(studentId, dto);
  }

  @Get()
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get all student settings' })
  async getAll(@Query() pagination: PaginationDto) {
    const [data, total] = await this.service.getAll(pagination);
    return { data, total, page: pagination.page, limit: pagination.limit };
  }

  @Delete('/:studentId')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('student', 'admin')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete student settings' })
  async delete(@Param('studentId') studentId: string) {
    await this.service.delete(studentId);
    return { message: 'Student settings deleted' };
  }
}
