"""Auto-converted from TypeScript.
Original file: crew-member-task/dto/stop-crew-member-task.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsString, IsNotEmpty, MinLength, MaxLength } from 'class-validator';

export class StopCrewMemberTaskDto {
  @IsString()
  @IsNotEmpty()
  reason: string;
}

'''
