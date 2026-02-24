"""Auto-converted from TypeScript.
Original file: task-incident/dto/bounding-box.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsNumber } from 'class-validator';

export class BoundingBoxDto {
  @IsNumber()
  x_min: number;

  @IsNumber()
  y_min: number;

  @IsNumber()
  x_max: number;

  @IsNumber()
  y_max: number;

  @IsNumber()
  width: number;

  @IsNumber()
  height: number;
}

'''
