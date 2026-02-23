"""Auto-converted from TypeScript.
Original file: drone-management/dto/create-drone.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsString, IsNotEmpty, IsNumber, IsDateString } from 'class-validator';
import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';

export class CreateDroneDto {
  @ApiProperty({
    description: 'The ID of the pilot this drone belongs to',
    example: 1,
  })
  @IsNumber()
  @IsNotEmpty()
  @Type(() => Number)
  onboardingId: number;

  @ApiProperty({
    description: 'The total number of drones a pilot has',
    example: 1,
  })
  @IsNumber()
  @IsNotEmpty()
  @Type(() => Number)
  numberOfDrones: number;

  @ApiProperty({ description: 'Drone make', example: 'DJI' })
  @IsString()
  @IsNotEmpty()
  droneMake: string;

  @ApiProperty({ description: 'Drone model', example: 'Phantom 4 Pro' })
  @IsString()
  @IsNotEmpty()
  droneModel: string;

  @ApiProperty({
    description: 'Unique drone serial number',
    example: 'DJI-XYZ-12345',
  })
  @IsString()
  @IsNotEmpty()
  droneSerialNumber: string;

  @ApiProperty({ description: 'Maximum camera resolution', example: '4K UHD' })
  @IsString()
  @IsNotEmpty()
  maxCameraResolution: string;

  @ApiProperty({ description: 'Maximum flight time', example: '30 minutes' })
  @IsString()
  @IsNotEmpty()
  maxFlightTime: string;

  @ApiProperty({ description: 'Number of backup batteries', example: 2 })
  @IsNumber()
  @IsNotEmpty()
  @Type(() => Number)
  numberOfBackupBattery: number;

  @ApiProperty({ description: 'License expiry date', example: '2025-12-31' })
  @IsDateString()
  @IsNotEmpty()
  licenseExpiryDate: string;
}

'''
