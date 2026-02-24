"""Auto-converted from TypeScript.
Original file: crew-member-task/dto/reject-crew-member-task.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsString, IsNotEmpty, MinLength, MaxLength } from 'class-validator';

export class RejectCrewMemberTaskDto {
  @IsString()
  @IsNotEmpty()
  reason: string;
}

'''
