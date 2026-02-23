"""Auto-converted from TypeScript.
Original file: task-incident/dto/create-incident-bulk.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Type } from 'class-transformer';
import {
  IsString,
  IsNotEmpty,
  IsEnum,
  IsArray,
  ValidateNested,
} from 'class-validator';
import { IncidentSeverity } from 'src/common/enum/incident-severity';
import { CreateTaskIncidentDto } from './create-task-incident.dto';

export class CreateTaskIncidentBulkDto {
  @IsString()
  @IsNotEmpty()
  taskId: string;

  @IsEnum(IncidentSeverity)
  severityLevel: IncidentSeverity;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => CreateTaskIncidentDto)
  items: CreateTaskIncidentDto[];
}

'''
