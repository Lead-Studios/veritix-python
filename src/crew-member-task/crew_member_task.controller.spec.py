"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-task.controller.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { CrewMemberTaskController } from './crew-member-task.controller';
import { CrewMemberTaskService } from './crew-member-task.service';

describe('CrewMemberTaskController', () => {
  let controller: CrewMemberTaskController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [CrewMemberTaskController],
      providers: [CrewMemberTaskService],
    }).compile();

    controller = module.get<CrewMemberTaskController>(CrewMemberTaskController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});

'''
