import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Issue02Product } from './issue-02.entity';
import { CreateIssue02Dto, UpdateIssue02Dto } from './issue-02.dto';

@Injectable()
export class Issue02Service {
  constructor(
    @InjectRepository(Issue02Product)
    private readonly repository: Repository<Issue02Product>,
  ) {}

  async create(dto: CreateIssue02Dto): Promise<Issue02Product> {
    const entity = this.repository.create(dto);
    return this.repository.save(entity);
  }

  async findAll(): Promise<Issue02Product[]> {
    return this.repository.find();
  }

  async findByCategory(category: string): Promise<Issue02Product[]> {
    return this.repository.find({ where: { category } });
  }

  async findOne(id: string): Promise<Issue02Product> {
    const entity = await this.repository.findOne({ where: { id } });
    if (!entity) {
      throw new NotFoundException(`Product with ID ${id} not found`);
    }
    return entity;
  }

  async update(id: string, dto: UpdateIssue02Dto): Promise<Issue02Product> {
    await this.findOne(id);
    await this.repository.update(id, dto);
    return this.findOne(id);
  }

  async remove(id: string): Promise<void> {
    const result = await this.repository.delete(id);
    if (result.affected === 0) {
      throw new NotFoundException(`Product with ID ${id} not found`);
    }
  }
}
