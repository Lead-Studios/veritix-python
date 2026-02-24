"""Auto-converted from TypeScript.
Original file: crew-member-task/dto/get-crew-member-tasks.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsOptional, IsEnum } from 'class-validator';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';
import { Type } from 'class-transformer';

export class GetCrewMemberTasksDto {
  @IsOptional()
  @IsEnum(FlightTaskStatus)
  status?: FlightTaskStatus;

  @IsOptional()
  @Type(() => Number)
  page?: number = 1;

  @IsOptional()
  @Type(() => Number)
  limit?: number = 10;

  @IsOptional()
  sortBy?: string = '-assignedAt';
}

'''
