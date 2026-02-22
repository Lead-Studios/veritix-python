import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AdminSettingsEntity } from './admin-settings.entity';
import { CreateAdminSettingsDto } from './dtos/create-admin-settings.dto';
import { PaginationDto } from '../../common/dtos/pagination.dto';

@Injectable()
export class AdminSettingsService {
  constructor(
    @InjectRepository(AdminSettingsEntity)
    private readonly repository: Repository<AdminSettingsEntity>,
  ) {}

  async create(adminId: string, dto: CreateAdminSettingsDto): Promise<AdminSettingsEntity> {
    const settings = this.repository.create({
      adminId,
      ...dto,
    });
    return this.repository.save(settings);
  }

  async findByAdmin(adminId: string): Promise<AdminSettingsEntity> {
    const settings = await this.repository.findOne({ where: { adminId } });
    if (!settings) {
      throw new NotFoundException('Admin settings not found');
    }
    return settings;
  }

  async update(adminId: string, dto: CreateAdminSettingsDto): Promise<AdminSettingsEntity> {
    const settings = await this.findByAdmin(adminId);
    Object.assign(settings, dto);
    return this.repository.save(settings);
  }

  async getAll(pagination: PaginationDto): Promise<[AdminSettingsEntity[], number]> {
    const skip = (pagination.page - 1) * pagination.limit;
    return this.repository.findAndCount({
      skip,
      take: pagination.limit,
    });
  }

  async delete(adminId: string): Promise<void> {
    const result = await this.repository.delete({ adminId });
    if (result.affected === 0) {
      throw new NotFoundException('Admin settings not found');
    }
  }
}
