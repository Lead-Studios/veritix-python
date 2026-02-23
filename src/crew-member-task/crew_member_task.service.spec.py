"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-task.service.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { CrewMemberTaskService } from './crew-member-task.service';

describe('CrewMemberTaskService', () => {
  let service: CrewMemberTaskService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [CrewMemberTaskService],
    }).compile();

    service = module.get<CrewMemberTaskService>(CrewMemberTaskService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});

'''
