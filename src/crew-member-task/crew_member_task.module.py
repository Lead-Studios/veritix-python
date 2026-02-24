"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-task.module.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Module } from '@nestjs/common';
import { CrewMemberTaskService } from './crew-member-task.service';
import { CrewMemberTaskController } from './crew-member-task.controller';
import { HttpModule } from '@nestjs/axios';
import { MongooseModule } from '@nestjs/mongoose';
import { JwtModule } from '@nestjs/jwt';
import { ConfigModule } from '@nestjs/config';
import { Incident, IncidentSchema } from 'src/task-incident/model/incident';
import { TaskImage, TaskImageSchema } from 'src/task-incident/model/task-image';
import { CrewMemberTask, CrewMemberTaskSchema } from './model/crew-member-task';
import { CrewMemberTaskFunction } from './helper/crew-member-task-function';
import { SubscriberFlightTaskModule } from 'src/subscriber-flight-task/subscriber-flight-task.module';
import { CrewMemberAuthModule } from 'src/crew-member-auth/crew-member-auth.module';
import { FileUploadModule } from 'src/config/upload/upload.module';
import {
  CrewMember,
  CrewMemberSchema,
} from 'src/crew-member-management/model/crew-member';
import {
  SubscriberFlightTask,
  SubscriberFlightTaskSchema,
} from 'src/subscriber-flight-task/model/subscriber-flight-task';
import {
  CrewMemberLocation,
  CrewMemberLocationSchema,
} from './model/crew-member-location';
import { CrewMemberLocationGateway } from './gateway/crew-member-location.gateway';
import { CrewMemberLocationService } from './crew-member-location.service';
import { EmailModule } from 'src/config/email/email.module';
import { User, UserSchema } from 'src/user-auth/model/user';
import { SubscriberTaskEmailFunction } from './helper/subscriber-task-email-function';

@Module({
  imports: [
    HttpModule,
    ConfigModule,
    JwtModule.register({}),
    MongooseModule.forFeature([
      { name: TaskImage.name, schema: TaskImageSchema },
      { name: Incident.name, schema: IncidentSchema },
      { name: CrewMemberTask.name, schema: CrewMemberTaskSchema },
      { name: CrewMember.name, schema: CrewMemberSchema },
      { name: SubscriberFlightTask.name, schema: SubscriberFlightTaskSchema },
      { name: CrewMemberLocation.name, schema: CrewMemberLocationSchema },
      { name: User.name, schema: UserSchema },
    ]),
    SubscriberFlightTaskModule,
    CrewMemberAuthModule,
    FileUploadModule,
    EmailModule,
  ],
  controllers: [CrewMemberTaskController],
  providers: [
    CrewMemberTaskService,
    CrewMemberTaskFunction,
    CrewMemberLocationGateway,
    CrewMemberLocationService,
    SubscriberTaskEmailFunction,
  ],
  exports: [CrewMemberLocationService],
})
export class CrewMemberTaskModule {}

'''
