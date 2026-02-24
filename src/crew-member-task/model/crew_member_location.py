"""Auto-converted from TypeScript.
Original file: crew-member-task/model/crew-member-location.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

export type CrewMemberLocationDocument = CrewMemberLocation & Document;

@Schema({ timestamps: true })
export class CrewMemberLocation {
  @Prop({ required: true })
  crewMemberId: number;

  @Prop({ required: true })
  taskId: string;

  @Prop({ required: true })
  latitude: number;

  @Prop({ required: true })
  longitude: number;

  @Prop({ type: Number, default: null })
  accuracy: number;

  @Prop({ type: Number, default: null })
  altitude: number;

  @Prop({ type: Number, default: null })
  speed: number;

  @Prop({ type: Number, default: null })
  heading: number;

  @Prop({ required: true })
  subscriberId: number;

  @Prop({ default: true })
  isActive: boolean;

  @Prop({ default: Date.now })
  lastUpdatedAt: Date;
}

export const CrewMemberLocationSchema =
  SchemaFactory.createForClass(CrewMemberLocation);

'''
