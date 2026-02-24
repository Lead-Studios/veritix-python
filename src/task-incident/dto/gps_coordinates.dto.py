"""Auto-converted from TypeScript.
Original file: task-incident/dto/gps-coordinates.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsNumber } from 'class-validator';

export class GpsCoordinatesDto {
  @IsNumber()
  latitude: number;

  @IsNumber()
  longitude: number;

  @IsNumber()
  altitude: number;

  @IsNumber()
  accuracy: number;
}

'''
