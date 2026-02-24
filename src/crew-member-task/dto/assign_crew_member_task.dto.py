"""Auto-converted from TypeScript.
Original file: crew-member-task/dto/assign-crew-member-task.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  IsEnum,
  IsNotEmpty,
  IsNumber,
  IsOptional,
  IsString,
  Matches,
} from 'class-validator';
import { TaskPriority } from 'src/common/enum/task-priority';

export class AssignCrewMemberTaskDto {
  @IsNumber()
  @IsNotEmpty()
  assignee: number;

  @IsString()
  @IsNotEmpty()
  @Matches(/^\d{4}-\d{2}-\d{2}$/, { message: 'flightDate must be YYYY-MM-DD' })
  dueDate: string;

  @IsString()
  @IsNotEmpty()
  @Matches(/^(0?[1-9]|1[0-2]):[0-5][0-9]\s?(AM|PM)$/i, {
    message: 'flightTime must be in the format HH:mm AM/PM',
  })
  dueTime: string;

  @IsOptional()
  @IsEnum(TaskPriority)
  priority?: TaskPriority;

  @IsOptional()
  @IsString()
  note?: string;
}

'''
