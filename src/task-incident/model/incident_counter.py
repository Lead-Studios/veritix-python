"""Auto-converted from TypeScript.
Original file: task-incident/model/incident-counter.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type IncidentCounterDocument = IncidentCounter & Document;

@Schema({ collection: 'incidentCounters' })
export class IncidentCounter {
  @Prop({ required: true, unique: true })
  key: string;

  @Prop({ required: true, default: 0 })
  value: number;
}

export const IncidentCounterSchema =
  SchemaFactory.createForClass(IncidentCounter);

'''
