"""Auto-converted from TypeScript.
Original file: task-incident/dto/retrieve-subscriber-incidents.query.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsEnum, IsInt, IsOptional, IsString, Min } from 'class-validator';
import { Type } from 'class-transformer';
import { IncidentStatus } from 'src/common/enum/incident-status';

export class RetrieveSubscriberIncidentsQuery {
  @ApiPropertyOptional({
    example: 1,
    description: 'Page number',
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  page?: number;

  @ApiPropertyOptional({
    example: 10,
    description: 'Items per page',
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  limit?: number;

  @ApiPropertyOptional({
    example: 'INC-ALL-001',
    description: 'Search by incident ID',
  })
  @IsOptional()
  @IsString()
  search?: string;

  @ApiPropertyOptional({
    enum: IncidentStatus,
    example: IncidentStatus.ASSIGNED_CREW_MEMBER,
    description: 'Filter by incident status',
  })
  @IsOptional()
  @IsEnum(IncidentStatus)
  status?: IncidentStatus;
}

'''
