"""Auto-converted from TypeScript.
Original file: task-incident/task-incident.service.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { TaskIncidentService } from './task-incident.service';

describe('TaskIncidentService', () => {
  let service: TaskIncidentService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [TaskIncidentService],
    }).compile();

    service = module.get<TaskIncidentService>(TaskIncidentService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});

'''
