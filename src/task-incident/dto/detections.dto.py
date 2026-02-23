"""Auto-converted from TypeScript.
Original file: task-incident/dto/detections.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsString, IsNumber, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { BoundingBoxDto } from './bounding-box.dto';
import { GpsCoordinatesDto } from './gps-coordinates.dto';

export class AiDetectionDto {
  @IsString()
  detection_id: string;

  @ValidateNested()
  @Type(() => BoundingBoxDto)
  bounding_box: BoundingBoxDto;

  @ValidateNested()
  @Type(() => GpsCoordinatesDto)
  gps_coordinates: GpsCoordinatesDto;

  @IsNumber()
  confidence_score: number;

  @IsNumber()
  area_pixels: number;

  @IsNumber()
  area_square_meters: number;

  @IsString()
  waste_type: string;
}

'''
