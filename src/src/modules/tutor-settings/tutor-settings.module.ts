import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TutorSettingsController } from './tutor-settings.controller';
import { TutorSettingsService } from './tutor-settings.service';
import { TutorSettingsEntity } from './tutor-settings.entity';

@Module({
  imports: [TypeOrmModule.forFeature([TutorSettingsEntity])],
  controllers: [TutorSettingsController],
  providers: [TutorSettingsService],
  exports: [TutorSettingsService],
})
export class TutorSettingsModule {}
