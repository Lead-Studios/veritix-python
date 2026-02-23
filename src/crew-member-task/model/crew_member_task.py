"""Auto-converted from TypeScript.
Original file: crew-member-task/model/crew-member-task.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';
import { TaskPriority } from 'src/common/enum/task-priority';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';

export type CrewMemberTaskDocument = CrewMemberTask & Document;
@Schema({ timestamps: true })
export class CrewMemberTask {
  @Prop({ type: String, ref: 'SubscriberFlightTask', required: true })
  taskId: string;

  @Prop({ required: true })
  crewMemberId: number;

  @Prop({ type: [Number], ref: 'TaskImage', required: true })
  imageAssigned: number[];

  @Prop({ required: true })
  assignedBy: number;

  @Prop({ type: Date, default: Date.now })
  assignedAt: Date;

  @Prop({ type: String, required: true })
  dueDate: string;

  @Prop({ type: String, required: true })
  dueTime: string;

  @Prop({ type: Date, required: true, index: true })
  dueDateTime: Date;

  @Prop({
    type: String,
    enum: TaskPriority,
    default: TaskPriority.NORMAL,
  })
  priority: TaskPriority;

  @Prop()
  note?: string;

  @Prop()
  rejectionReason?: string;

  @Prop()
  stoppedReason?: string;

  @Prop({ type: [String], default: [] })
  completionEvidence?: string[];

  @Prop({
    type: String,
    enum: FlightTaskStatus,
    default: FlightTaskStatus.ASSIGNED_CREW_MEMBER,
  })
  status: FlightTaskStatus;

  @Prop()
  location: string;

  @Prop({
    type: {
      latitude: { type: Number },
      longitude: { type: Number },
    },
    _id: false,
  })
  gpsCoordinates?: {
    latitude: number;
    longitude: number;
  };

  @Prop({ type: Date, default: null })
  acceptedAt?: Date;

  @Prop({ type: Date, default: null })
  begunAt?: Date;

  @Prop({ type: Date, default: null })
  stoppedAt?: Date;

  @Prop({ type: Date, default: null })
  rejectedAt?: Date;

  @Prop({ type: Date, default: null })
  completedAt?: Date;
}

export const CrewMemberTaskSchema =
  SchemaFactory.createForClass(CrewMemberTask);

CrewMemberTaskSchema.index({ taskId: 1, crewMemberId: 1 }, { unique: true });

'''
