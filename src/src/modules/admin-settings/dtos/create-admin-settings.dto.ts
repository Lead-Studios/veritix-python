import { IsString, IsOptional, IsBoolean } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateAdminSettingsDto {
  @ApiProperty({ description: 'Email notifications enabled' })
  @IsOptional()
  @IsBoolean()
  emailNotifications?: boolean;

  @ApiProperty({ description: 'Admin permissions' })
  @IsOptional()
  @IsString()
  permissions?: string;

  @ApiProperty({ description: 'Two-factor authentication enabled' })
  @IsOptional()
  @IsBoolean()
  twoFactorEnabled?: boolean;

  @ApiProperty({ description: 'Avatar URL' })
  @IsOptional()
  @IsString()
  avatar?: string;
}
