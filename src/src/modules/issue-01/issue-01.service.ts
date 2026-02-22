import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Issue01UserProfile } from './issue-01.entity';
import { CreateIssue01Dto, UpdateIssue01Dto } from './issue-01.dto';

@Injectable()
export class Issue01Service {
  constructor(
    @InjectRepository(Issue01UserProfile)
    private readonly repository: Repository<Issue01UserProfile>,
  ) {}

  async create(dto: CreateIssue01Dto): Promise<Issue01UserProfile> {
    const entity = this.repository.create(dto);
    return this.repository.save(entity);
  }

  async findAll(): Promise<Issue01UserProfile[]> {
    return this.repository.find();
  }

  async findOne(id: string): Promise<Issue01UserProfile> {
    const entity = await this.repository.findOne({ where: { id } });
    if (!entity) {
      throw new NotFoundException(`User Profile with ID ${id} not found`);
    }
    return entity;
  }

  async update(id: string, dto: UpdateIssue01Dto): Promise<Issue01UserProfile> {
    await this.findOne(id);
    await this.repository.update(id, dto);
    return this.findOne(id);
  }

  async remove(id: string): Promise<void> {
    const result = await this.repository.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`User Profile with ID ${id} not found`);
    }
  }
}
