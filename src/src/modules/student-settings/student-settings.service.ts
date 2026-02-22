import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { StudentSettingsEntity } from './student-settings.entity';
import { CreateStudentSettingsDto } from './dtos/create-student-settings.dto';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@Injectable()
export class StudentSettingsService {
  constructor(
    @InjectRepository(StudentSettingsEntity)
    private readonly repository: Repository<StudentSettingsEntity>,
  ) {}

  async create(studentId: string, dto: CreateStudentSettingsDto): Promise<StudentSettingsEntity> {
    const settings = this.repository.create({
      studentId,
      ...dto,
    });
    return this.repository.save(settings);
  }

  async findByStudent(studentId: string): Promise<StudentSettingsEntity> {
    const settings = await this.repository.findOne({ where: { studentId } });
    if (!settings) {
      throw new NotFoundException('Student settings not found');
    }
    return settings;
  }

  async update(studentId: string, dto: CreateStudentSettingsDto): Promise<StudentSettingsEntity> {
    const settings = await this.findByStudent(studentId);
    Object.assign(settings, dto);
    return this.repository.save(settings);
  }

  async getAll(pagination: PaginationDto): Promise<[StudentSettingsEntity[], number]> {
    const skip = (pagination.page - 1) * pagination.limit;
    return this.repository.findAndCount({
      skip,
      take: pagination.limit,
    });
  }

  async delete(studentId: string): Promise<void> {
    const result = await this.repository.delete({ studentId });
    if (result.affected === 0) {
      throw new NotFoundException('Student settings not found');
    }
  }
}
