"""Auto-converted from TypeScript.
Original file: drone-management/drone-management.module.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { DroneService } from './drone-management.service';
import { DroneController } from './drone-management.controller';
import { Drone, DroneSchema } from './model/drone';
import {
  PilotOnboarding,
  PilotOnboardingSchema,
} from '../pilot-onboarding/model/pilot-onboarding';
import { EmailModule } from 'src/config/email/email.module';
import { FileUploadModule } from 'src/config/upload/upload.module';
import { PilotEmailFunctions } from 'src/pilot-onboarding/Helper/pilot-email-function';
import {
  PilotTaskFlight,
  PilotTaskFlightSchema,
} from 'src/pilot-flight-task/model/pilot-flight-task';
import {
  PilotDroneFootages,
  PilotDroneFootageSchema,
} from 'src/pilot-drone-footages/model/pilot-drone-footages';
import { Incident, IncidentSchema } from 'src/task-incident/model/incident';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: Drone.name, schema: DroneSchema },
      { name: PilotOnboarding.name, schema: PilotOnboardingSchema },
      { name: PilotTaskFlight.name, schema: PilotTaskFlightSchema },
      { name: PilotDroneFootages.name, schema: PilotDroneFootageSchema },
      { name: Incident.name, schema: IncidentSchema },
    ]),
    EmailModule,
    FileUploadModule,
  ],
  controllers: [DroneController],
  providers: [DroneService, PilotEmailFunctions],
  exports: [DroneService],
})
export class DroneManagementModule {}

'''
