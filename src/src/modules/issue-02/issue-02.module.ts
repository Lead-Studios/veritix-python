import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Issue02Controller } from './issue-02.controller';
import { Issue02Service } from './issue-02.service';
import { Issue02Product } from './issue-02.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Issue02Product])],
  controllers: [Issue02Controller],
  providers: [Issue02Service],
  exports: [Issue02Service],
})
export class Issue02Module {}
