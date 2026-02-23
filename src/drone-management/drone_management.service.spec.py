"""Auto-converted from TypeScript.
Original file: drone-management/drone-management.service.spec.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Test, TestingModule } from '@nestjs/testing';
import { DroneService } from './drone-management.service';

describe('DroneService', () => {
  let service: DroneService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [DroneService],
    }).compile();

    service = module.get<DroneService>(DroneService);
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });
});

'''
