import { IsString, IsOptional, IsBoolean } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateStudentSettingsDto {
  @ApiProperty({ description: 'Email notifications enabled' })
  @IsOptional()
  @IsBoolean()
  emailNotifications?: boolean;

  @ApiProperty({ description: 'Course reminders enabled' })
  @IsOptional()
  @IsBoolean()
  courseReminders?: boolean;

  @ApiProperty({ description: 'Push notifications enabled' })
  @IsOptional()
  @IsBoolean()
  pushNotifications?: boolean;

  @ApiProperty({ description: 'Preferred language' })
  @IsOptional()
  @IsString()
  preferredLanguage?: string;

  @ApiProperty({ description: 'Timezone' })
  @IsOptional()
  @IsString()
  timezone?: string;

  @ApiProperty({ description: 'Display public profile' })
  @IsOptional()
  @IsBoolean()
  displayProfile?: boolean;

  @ApiProperty({ description: 'Student bio' })
  @IsOptional()
  @IsString()
  bio?: string;

  @ApiProperty({ description: 'Avatar URL' })
  @IsOptional()
  @IsString()
  avatar?: string;

  @ApiProperty({ description: 'Two-factor authentication enabled' })
  @IsOptional()
  @IsBoolean()
  twoFactorEnabled?: boolean;
}
