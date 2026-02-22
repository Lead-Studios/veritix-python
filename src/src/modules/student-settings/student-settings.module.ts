import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { StudentSettingsController } from './student-settings.controller';
import { StudentSettingsService } from './student-settings.service';
import { StudentSettingsEntity } from './student-settings.entity';

@Module({
  imports: [TypeOrmModule.forFeature([StudentSettingsEntity])],
  controllers: [StudentSettingsController],
  providers: [StudentSettingsService],
  exports: [StudentSettingsService],
})
export class StudentSettingsModule {}
