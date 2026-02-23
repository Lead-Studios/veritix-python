"""Auto-converted from TypeScript.
Original file: task-incident/dto/create-multiple-task-incident.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsArray, IsNotEmpty, IsString, ValidateNested } from 'class-validator';
import { Type } from 'class-transformer';
import { CreateTaskIncidentDto } from './create-task-incident.dto';

export class CreateMultipleTaskIncidentDto {
  @IsString()
  @IsNotEmpty()
  taskId: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CreateTaskIncidentDto)
  images: CreateTaskIncidentDto[];
}

'''
