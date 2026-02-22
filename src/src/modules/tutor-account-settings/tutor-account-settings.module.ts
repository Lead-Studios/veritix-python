import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from '../../entities/user.entity';
import { TutorAccountSettingsService } from './tutor-account-settings.service';
import { TutorAccountSettingsController } from './tutor-account-settings.controller';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  controllers: [TutorAccountSettingsController],
  providers: [TutorAccountSettingsService],
  exports: [TutorAccountSettingsService],
})
export class TutorAccountSettingsModule {}
