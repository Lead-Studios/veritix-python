import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Issue01Controller } from './issue-01.controller';
import { Issue01Service } from './issue-01.service';
import { Issue01UserProfile } from './issue-01.entity';

@Module({
  imports: [TypeOrmModule.forFeature([Issue01UserProfile])],
  controllers: [Issue01Controller],
  providers: [Issue01Service],
  exports: [Issue01Service],
})
export class Issue01Module {}
