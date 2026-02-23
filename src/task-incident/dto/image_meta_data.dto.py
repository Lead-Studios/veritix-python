"""Auto-converted from TypeScript.
Original file: task-incident/dto/image-meta-data.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsString, IsNumber, IsDateString, IsNotEmpty } from 'class-validator';

export class ImageMetadataDto {
  @IsString()
  @IsNotEmpty()
  filename: string;

  @IsString()
  @IsNotEmpty()
  s3_bucket: string;

  @IsString()
  @IsNotEmpty()
  s3_filename: string;

  @IsString()
  @IsNotEmpty()
  imageUrl: string;

  @IsDateString()
  @IsNotEmpty()
  capture_timestamp: string;

  @IsNumber()
  @IsNotEmpty()
  image_width: number;

  @IsNumber()
  @IsNotEmpty()
  image_height: number;
}

'''
