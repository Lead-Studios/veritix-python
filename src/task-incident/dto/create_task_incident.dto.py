"""Auto-converted from TypeScript.
Original file: task-incident/dto/create-task-incident.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  IsString,
  IsArray,
  IsNumber,
  ValidateNested,
  IsOptional,
  IsEnum,
  IsNotEmpty,
} from 'class-validator';
import { Type } from 'class-transformer';
import { AiDetectionDto } from './detections.dto';
import { ImageMetadataDto } from './image-meta-data.dto';
import { IncidentSeverity } from 'src/common/enum/incident-severity';

export class CreateTaskIncidentDto {
  @IsString()
  @IsNotEmpty()
  taskId: string;

  @IsEnum(IncidentSeverity)
  @IsNotEmpty()
  severityLevel: IncidentSeverity;

  @ValidateNested()
  @Type(() => ImageMetadataDto)
  imageMetadata: ImageMetadataDto;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => AiDetectionDto)
  detections: AiDetectionDto[];

  @IsNumber()
  @IsNotEmpty()
  totalDetections: number;

  @IsNumber()
  @IsNotEmpty()
  totalWasteAreaPixels: number;

  @IsNumber()
  @IsNotEmpty()
  totalWasteAreaSquareMeters: number;

  @IsNumber()
  @IsNotEmpty()
  processingDurationMs: number;

  @IsOptional()
  @IsString()
  modelVersion: string;

  @IsString()
  @IsNotEmpty()
  status: string;

  @IsOptional()
  @IsString()
  errorMessage?: string | null;
}

'''
