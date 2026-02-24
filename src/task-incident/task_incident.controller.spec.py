"""Auto-converted from TypeScript.
Original file: task-incident/task-incident.controller.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { TaskIncidentController } from './task-incident.controller';
import { TaskIncidentService } from './task-incident.service';

describe('TaskIncidentController', () => {
  let controller: TaskIncidentController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [TaskIncidentController],
      providers: [TaskIncidentService],
    }).compile();

    controller = module.get<TaskIncidentController>(TaskIncidentController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});

'''
