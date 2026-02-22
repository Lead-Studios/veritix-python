import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  UseGuards,
  Req,
  HttpStatus,
  HttpCode,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { CoursesService } from './courses.service';
import { CreateCourseDto, UpdateCourseDto, CourseFilterDto } from './dtos/create-course.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';

@ApiTags('Courses')
@Controller('courses')
export class CoursesController {
  constructor(private readonly coursesService: CoursesService) {}

  @Get()
  @ApiOperation({ summary: 'Get all courses with filters' })
  @ApiResponse({ status: 200, description: 'Courses retrieved successfully' })
  async findAll(@Query() filter: CourseFilterDto) {
    return this.coursesService.findAll(filter);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get course by ID' })
  @ApiResponse({ status: 200, description: 'Course retrieved successfully' })
  @ApiResponse({ status: 404, description: 'Course not found' })
  async findById(@Param('id') id: string) {
    return this.coursesService.findById(id);
  }

  @Post()
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Create new course' })
  @HttpCode(HttpStatus.CREATED)
  async create(@Body() dto: CreateCourseDto, @Req() req) {
    const tutorId = req.user.sub;
    return this.coursesService.create(dto, tutorId);
  }

  @Put(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update course' })
  async update(
    @Param('id') id: string,
    @Body() dto: UpdateCourseDto,
    @Req() req,
  ) {
    const tutorId = req.user.sub;
    return this.coursesService.update(id, dto, tutorId);
  }

  @Post(':id/publish')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Publish course' })
  async publish(@Param('id') id: string, @Req() req) {
    const tutorId = req.user.sub;
    return this.coursesService.publishCourse(id, tutorId);
  }

  @Delete(':id')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Delete course' })
  @HttpCode(HttpStatus.NO_CONTENT)
  async delete(@Param('id') id: string, @Req() req) {
    const tutorId = req.user.sub;
    return this.coursesService.delete(id, tutorId);
  }

  @Get('tutor/my-courses')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get my courses (tutor)' })
  async getTutorCourses(@Req() req) {
    const tutorId = req.user.sub;
    return this.coursesService.getTutorCourses(tutorId);
  }
}
