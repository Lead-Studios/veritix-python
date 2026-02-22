import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { TutorSettingsEntity } from './tutor-settings.entity';
import { CreateTutorSettingsDto } from './dtos/create-tutor-settings.dto';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@Injectable()
export class TutorSettingsService {
  constructor(
    @InjectRepository(TutorSettingsEntity)
    private readonly repository: Repository<TutorSettingsEntity>,
  ) {}

  async create(tutorId: string, dto: CreateTutorSettingsDto): Promise<TutorSettingsEntity> {
    const settings = this.repository.create({
      tutorId,
      ...dto,
    });
    return this.repository.save(settings);
  }

  async findByTutor(tutorId: string): Promise<TutorSettingsEntity> {
    const settings = await this.repository.findOne({ where: { tutorId } });
    if (!settings) {
      throw new NotFoundException('Tutor settings not found');
    }
    return settings;
  }

  async update(tutorId: string, dto: CreateTutorSettingsDto): Promise<TutorSettingsEntity> {
    const settings = await this.findByTutor(tutorId);
    Object.assign(settings, dto);
    return this.repository.save(settings);
  }

  async getAll(pagination: PaginationDto): Promise<[TutorSettingsEntity[], number]> {
    const skip = (pagination.page - 1) * pagination.limit;
    return this.repository.findAndCount({
      skip,
      take: pagination.limit,
    });
  }

  async delete(tutorId: string): Promise<void> {
    const result = await this.repository.delete({ tutorId });
    if (result.affected === 0) {
      throw new NotFoundException('Tutor settings not found');
    }
  }
}
