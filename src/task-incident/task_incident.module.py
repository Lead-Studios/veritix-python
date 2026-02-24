"""Auto-converted from TypeScript.
Original file: task-incident/task-incident.module.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Module } from '@nestjs/common';
import { TaskIncidentService } from './task-incident.service';
import { TaskIncidentController } from './task-incident.controller';
import { HttpModule } from '@nestjs/axios';
import { MongooseModule } from '@nestjs/mongoose';
import {
  IncidentCounter,
  IncidentCounterSchema,
} from './model/incident-counter';
import { TaskImage, TaskImageSchema } from './model/task-image';
import { Incident, IncidentSchema } from './model/incident';
import {
  PilotTaskFlight,
  PilotTaskFlightSchema,
} from 'src/pilot-flight-task/model/pilot-flight-task';
import { IncidentFunction } from './helper/incident-function';
import {
  SubscriberFlightTask,
  SubscriberFlightTaskSchema,
} from 'src/subscriber-flight-task/model/subscriber-flight-task';
import {
  CrewMemberTask,
  CrewMemberTaskSchema,
} from 'src/crew-member-task/model/crew-member-task';
import {
  CrewMember,
  CrewMemberSchema,
} from 'src/crew-member-management/model/crew-member';
import { IncidentEmailFunctions } from './helper/incident-email-function';
import { EmailModule } from 'src/config/email/email.module';
import { User, UserSchema } from 'src/user-auth/model/user';

@Module({
  imports: [
    HttpModule,
    MongooseModule.forFeature([
      { name: IncidentCounter.name, schema: IncidentCounterSchema },
      { name: TaskImage.name, schema: TaskImageSchema },
      { name: Incident.name, schema: IncidentSchema },
      { name: PilotTaskFlight.name, schema: PilotTaskFlightSchema },
      { name: SubscriberFlightTask.name, schema: SubscriberFlightTaskSchema },
      { name: CrewMemberTask.name, schema: CrewMemberTaskSchema },
      { name: CrewMember.name, schema: CrewMemberSchema },
      { name: User.name, schema: UserSchema },
    ]),
    EmailModule,
  ],
  controllers: [TaskIncidentController],
  providers: [TaskIncidentService, IncidentFunction, IncidentEmailFunctions],
})
export class TaskIncidentModule {}

'''
