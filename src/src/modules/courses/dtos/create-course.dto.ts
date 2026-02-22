import { IsString, IsNumber, IsOptional, IsEnum, Min } from 'class-validator';
import { CourseLevel } from '../entities/course.entity';

export class CreateCourseDto {
  @IsString()
  title: string;

  @IsString()
  description: string;

  @IsString()
  category: string;

  @IsEnum(CourseLevel)
  @IsOptional()
  level?: CourseLevel;

  @IsNumber()
  @Min(0)
  price: number;

  @IsNumber()
  @Min(1)
  duration: number;

  @IsString()
  @IsOptional()
  imageUrl?: string;

  @IsString()
  @IsOptional()
  prerequisites?: string;

  @IsString()
  @IsOptional()
  learningOutcomes?: string;
}

export class UpdateCourseDto {
  @IsString()
  @IsOptional()
  title?: string;

  @IsString()
  @IsOptional()
  description?: string;

  @IsString()
  @IsOptional()
  category?: string;

  @IsEnum(CourseLevel)
  @IsOptional()
  level?: CourseLevel;

  @IsNumber()
  @IsOptional()
  price?: number;

  @IsNumber()
  @IsOptional()
  duration?: number;

  @IsString()
  @IsOptional()
  imageUrl?: string;

  @IsString()
  @IsOptional()
  prerequisites?: string;

  @IsString()
  @IsOptional()
  learningOutcomes?: string;
}

export class CourseFilterDto {
  @IsString()
  @IsOptional()
  category?: string;

  @IsEnum(CourseLevel)
  @IsOptional()
  level?: CourseLevel;

  @IsNumber()
  @IsOptional()
  minPrice?: number;

  @IsNumber()
  @IsOptional()
  maxPrice?: number;

  @IsString()
  @IsOptional()
  searchTerm?: string;

  @IsNumber()
  @IsOptional()
  page: number = 1;

  @IsNumber()
  @IsOptional()
  pageSize: number = 10;
}
