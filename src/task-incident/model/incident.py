"""Auto-converted from TypeScript.
Original file: task-incident/model/incident.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';
import { IncidentSeverity } from 'src/common/enum/incident-severity';
import { IncidentStatus } from 'src/common/enum/incident-status';
import { MLRunStatus } from 'src/common/enum/ml-run-status';

export type IncidentDocument = Incident & Document;

@Schema({ timestamps: true, collection: 'incidents' })
export class Incident {
  @Prop({ required: true, unique: true })
  incidentId: string;

  @Prop({ required: true, ref: 'SubscriberFlightTask' })
  taskId: string;

  @Prop({ type: Number, ref: 'User', required: true })
  pilotId: number;

  @Prop({ type: Number, ref: 'User', required: true })
  subscriberId: number;

  @Prop({ required: true, ref: 'TaskImage' })
  imageId: number;

  @Prop({ required: true })
  wasteType: string;

  @Prop({
    type: String,
    enum: IncidentSeverity,
    default: IncidentSeverity.HIGH,
  })
  severityLevel: string;

  @Prop({ required: true })
  confidenceScore: number;

  @Prop({ required: false })
  modelVersion: string;

  @Prop({ required: true })
  processingDurationMs: number;

  @Prop({ required: true })
  areaPixels: number;

  @Prop({ required: true })
  areaSquareMeters: number;

  @Prop({
    type: {
      xMin: Number,
      yMin: Number,
      xMax: Number,
      yMax: Number,
      width: Number,
      height: Number,
    },
    required: true,
  })
  boundingBox: Record<string, number>;

  @Prop({
    type: {
      latitude: Number,
      longitude: Number,
      altitude: Number,
      accuracy: Number,
    },
    required: true,
  })
  gpsCoordinates: Record<string, number>;

  @Prop({
    type: String,
    enum: IncidentStatus,
    default: IncidentStatus.PENDING,
  })
  status: IncidentStatus;
  @Prop({
    type: String,
    enum: MLRunStatus,
    default: MLRunStatus.PROCESSED,
  })
  MLRunStatus: string;

  @Prop()
  createdAt: Date;

  @Prop()
  updatedAt: Date;

  @Prop({ type: String, ref: 'User' })
  assignedCrewId?: string;

  @Prop()
  assignedAt?: Date;
}

export const IncidentSchema = SchemaFactory.createForClass(Incident);
IncidentSchema.index({ taskId: 1 });
IncidentSchema.index({ pilotId: 1 });
IncidentSchema.index({ imageId: 1 });
IncidentSchema.index({ status: 1 });

'''
