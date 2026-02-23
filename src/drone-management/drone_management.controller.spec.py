"""Auto-converted from TypeScript.
Original file: drone-management/drone-management.controller.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { DroneController } from './drone-management.controller';
import { DroneService } from './drone-management.service';

describe('DroneController', () => {
  let controller: DroneController;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      controllers: [DroneController],
      providers: [DroneService],
    }).compile();

    controller = module.get<DroneController>(DroneController);
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });
});

'''
