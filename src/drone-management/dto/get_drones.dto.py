"""Auto-converted from TypeScript.
Original file: drone-management/dto/get-drones.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsOptional, IsString, IsEnum, IsInt, Min } from 'class-validator';
import { Type } from 'class-transformer';
import { PaginationQueryDto } from '../../common/pagination/dto/pagination-query.dto';
import { DroneStatus } from '../../common/enum/drone-status';

export class GetDronesDto extends PaginationQueryDto {
  @ApiPropertyOptional({
    description: 'Search by drone ID, make, model, or serial number',
    example: 'DJI',
  })
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({
    enum: DroneStatus,
    description: 'Filter by drone status',
    example: DroneStatus.ACTIVE,
  })
  @IsOptional()
  @IsEnum(DroneStatus)
  status?: DroneStatus;

  @ApiPropertyOptional({
    description: 'Filter by pilot onboarding ID',
    example: 1,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  pilotId?: number;

  @ApiPropertyOptional({
    description: 'Filter by drone make',
    example: 'DJI',
  })
  @IsOptional()
  @IsString()
  droneMake?: string;

  @ApiPropertyOptional({
    description: 'Filter by drone model',
    example: 'Phantom 4 Pro',
  })
  @IsOptional()
  @IsString()
  droneModel?: string;
}

'''
