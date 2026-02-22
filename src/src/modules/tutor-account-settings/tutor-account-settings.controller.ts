import { Controller, Get, Patch, Body, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiBearerAuth } from '@nestjs/swagger';
import { TutorAccountSettingsService } from './tutor-account-settings.service';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { Roles } from '../../auth/decorators/roles.decorator';
import { RolesGuard } from '../../auth/guards/roles.guard';

@ApiTags('Tutor Account Settings')
@Controller('tutor/account-settings')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('tutor')
@ApiBearerAuth()
export class TutorAccountSettingsController {
  constructor(private readonly settingsService: TutorAccountSettingsService) {}

  @Get()
  async getSettings(@Request() req) {
    return this.settingsService.getTutorSettings(req.user.userId);
  }

  @Patch()
  async updateSettings(@Body() updateData: any, @Request() req) {
    return this.settingsService.updateTutorSettings(req.user.userId, updateData);
  }

  @Get('notifications')
  async getNotificationSettings(@Request() req) {
    return this.settingsService.getTutorNotificationSettings(req.user.userId);
  }

  @Patch('notifications')
  async updateNotificationSettings(@Body() settings: any, @Request() req) {
    return this.settingsService.updateTutorNotificationSettings(req.user.userId, settings);
  }
}
