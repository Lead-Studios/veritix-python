"""Auto-converted from TypeScript.
Original file: crew-member-task/dto/complete-crew-member-task.dto.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IsNotEmpty, ArrayMaxSize } from 'class-validator';

export class CompleteCrewMemberTaskDto {
  @IsNotEmpty()
  @ArrayMaxSize(5, { message: 'Maximum 5 files allowed' })
  evidenceFiles: Express.Multer.File[];
}

'''
