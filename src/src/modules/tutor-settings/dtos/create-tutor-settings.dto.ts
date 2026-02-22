import { IsString, IsOptional, IsBoolean, IsNumber, Min, Max } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';

export class CreateTutorSettingsDto {
  @ApiProperty({ description: 'Tutor bio' })
  @IsOptional()
  @IsString()
  bio?: string;

  @ApiProperty({ description: 'Specializations' })
  @IsOptional()
  @IsString()
  specializations?: string;

  @ApiProperty({ description: 'Enable email notifications' })
  @IsOptional()
  @IsBoolean()
  emailNotifications?: boolean;

  @ApiProperty({ description: 'Enable SMS notifications' })
  @IsOptional()
  @IsBoolean()
  smsNotifications?: boolean;

  @ApiProperty({ description: 'Timezone' })
  @IsOptional()
  @IsString()
  timezone?: string;

  @ApiProperty({ description: 'Hourly rate' })
  @IsOptional()
  @IsNumber()
  @Min(10)
  @Max(500)
  hourlyRate?: number;

  @ApiProperty({ description: 'Is available' })
  @IsOptional()
  @IsBoolean()
  isAvailable?: boolean;

  @ApiProperty({ description: 'Avatar URL' })
  @IsOptional()
  @IsString()
  avatar?: string;
}
