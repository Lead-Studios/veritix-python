import {
  Injectable,
  NotFoundException,
  BadRequestException,
  ForbiddenException,
  Logger,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like } from 'typeorm';
import { Course, CourseStatus } from './entities/course.entity';
import { CreateCourseDto, UpdateCourseDto, CourseFilterDto } from './dtos/create-course.dto';

@Injectable()
export class CoursesService {
  private readonly logger = new Logger(CoursesService.name);

  constructor(
    @InjectRepository(Course)
    private coursesRepository: Repository<Course>,
  ) {}

  async create(dto: CreateCourseDto, tutorId: string): Promise<Course> {
    try {
      const course = this.coursesRepository.create({
        ...dto,
        tutorId,
        status: CourseStatus.DRAFT,
      });

      const savedCourse = await this.coursesRepository.save(course);
      this.logger.log(`Course created: ${savedCourse.id} by tutor: ${tutorId}`);

      return savedCourse;
    } catch (error) {
      this.logger.error(`Failed to create course: ${error.message}`);
      throw error;
    }
  }

  async findAll(filter: CourseFilterDto): Promise<{
    data: Course[];
    total: number;
    page: number;
    pageSize: number;
  }> {
    try {
      const query = this.coursesRepository.createQueryBuilder('course');

      // Filter by status
      query.where('course.status = :status', { status: CourseStatus.PUBLISHED });

      // Filter by category
      if (filter.category) {
        query.andWhere('course.category = :category', { category: filter.category });
      }

      // Filter by level
      if (filter.level) {
        query.andWhere('course.level = :level', { level: filter.level });
      }

      // Filter by price range
      if (filter.minPrice !== undefined) {
        query.andWhere('course.price >= :minPrice', { minPrice: filter.minPrice });
      }

      if (filter.maxPrice !== undefined) {
        query.andWhere('course.price <= :maxPrice', { maxPrice: filter.maxPrice });
      }

      // Search by title or description
      if (filter.searchTerm) {
        query.andWhere(
          '(course.title LIKE :search OR course.description LIKE :search)',
          { search: `%${filter.searchTerm}%` },
        );
      }

      // Pagination
      const page = filter.page || 1;
      const pageSize = filter.pageSize || 10;
      const skip = (page - 1) * pageSize;

      const [data, total] = await query
        .leftJoinAndSelect('course.tutor', 'tutor')
        .skip(skip)
        .take(pageSize)
        .orderBy('course.createdAt', 'DESC')
        .getManyAndCount();

      return { data, total, page, pageSize };
    } catch (error) {
      this.logger.error(`Failed to fetch courses: ${error.message}`);
      throw error;
    }
  }

  async findById(id: string): Promise<Course> {
    try {
      const course = await this.coursesRepository.findOne(id, {
        relations: ['tutor'],
      });

      if (!course) {
        throw new NotFoundException(`Course with ID ${id} not found`);
      }

      return course;
    } catch (error) {
      this.logger.error(`Failed to fetch course: ${error.message}`);
      throw error;
    }
  }

  async update(
    id: string,
    dto: UpdateCourseDto,
    tutorId: string,
  ): Promise<Course> {
    try {
      const course = await this.findById(id);

      // Verify ownership
      if (course.tutorId !== tutorId) {
        throw new ForbiddenException(
          'You do not have permission to update this course',
        );
      }

      Object.assign(course, dto);
      const updatedCourse = await this.coursesRepository.save(course);

      this.logger.log(`Course updated: ${id}`);

      return updatedCourse;
    } catch (error) {
      this.logger.error(`Failed to update course: ${error.message}`);
      throw error;
    }
  }

  async publishCourse(id: string, tutorId: string): Promise<Course> {
    try {
      const course = await this.findById(id);

      if (course.tutorId !== tutorId) {
        throw new ForbiddenException(
          'You do not have permission to publish this course',
        );
      }

      if (!course.title || !course.description || !course.price) {
        throw new BadRequestException(
          'Course must have title, description, and price to publish',
        );
      }

      course.status = CourseStatus.PUBLISHED;
      const publishedCourse = await this.coursesRepository.save(course);

      this.logger.log(`Course published: ${id}`);

      return publishedCourse;
    } catch (error) {
      this.logger.error(`Failed to publish course: ${error.message}`);
      throw error;
    }
  }

  async delete(id: string, tutorId: string): Promise<void> {
    try {
      const course = await this.findById(id);

      if (course.tutorId !== tutorId) {
        throw new ForbiddenException(
          'You do not have permission to delete this course',
        );
      }

      await this.coursesRepository.remove(course);

      this.logger.log(`Course deleted: ${id}`);
    } catch (error) {
      this.logger.error(`Failed to delete course: ${error.message}`);
      throw error;
    }
  }

  async getTutorCourses(tutorId: string): Promise<Course[]> {
    try {
      return await this.coursesRepository.find({
        where: { tutorId },
        order: { createdAt: 'DESC' },
      });
    } catch (error) {
      this.logger.error(`Failed to fetch tutor courses: ${error.message}`);
      throw error;
    }
  }
}
