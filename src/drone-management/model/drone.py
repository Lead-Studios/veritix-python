"""Auto-converted from TypeScript.
Original file: drone-management/model/drone.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types } from 'mongoose';
import { DroneStatus } from '../../common/enum/drone-status';

export type DroneDocument = Drone & Document;

@Schema({ timestamps: true, collection: 'Drones' })
export class Drone {
  @Prop({ unique: true })
  droneId: string;

  @Prop({ type: Number, ref: 'PilotOnboarding', required: true })
  pilot: number;

  @Prop({ required: true })
  droneMake: string;

  @Prop({ required: true })
  droneModel: string;

  @Prop({ required: true, unique: true })
  droneSerialNumber: string;

  @Prop({ required: true })
  maxCameraResolution: string;

  @Prop({ required: true })
  maxFlightTime: string;

  @Prop({ required: true })
  numberOfBackupBattery: number;

  @Prop({ required: true })
  ncaaCertificationImage: string;

  @Prop({ required: true })
  licenseExpiryDate: Date;

  @Prop({ required: false, default: false })
  isFlag?: boolean;

  @Prop({ required: false, default: false })
  isGrounded?: boolean;

  @Prop({
    type: String,
    enum: DroneStatus,
    default: DroneStatus.IN_REVIEW,
  })
  status: DroneStatus;

  @Prop({ type: Number, default: 0 })
  distanceCovered: number;

  @Prop({ type: Number, default: 0 })
  numberOfActiveFlights: number;

  @Prop({ type: Number, default: 0 })
  totalFlightHours: number;

  @Prop({ type: [String], default: [] })
  areas: string[];

  @Prop()
  createdAt: Date;

  @Prop()
  updatedAt: Date;

  id?: string;
}

export const DroneSchema = SchemaFactory.createForClass(Drone);

DroneSchema.pre<DroneDocument>('save', async function (next) {
  if (this.isNew) {
    const lastDrone = await this.model('Drone')
      .findOne({}, { droneId: 1 })
      .sort({ createdAt: -1 })
      .lean<{ droneId: string }>();

    let newNumber = 1;
    if (lastDrone?.droneId) {
      const match = lastDrone.droneId.match(/^LSDR-(\d{3})$/);
      if (match && match[1]) {
        newNumber = parseInt(match[1], 10) + 1;
      }
    }

    this.droneId = `LSDR-${newNumber.toString().padStart(3, '0')}`;
  }

  next();
});

DroneSchema.virtual('id').get(function (this: DroneDocument) {
  return (this._id as Types.ObjectId).toHexString();
});

DroneSchema.set('toJSON', {
  virtuals: true,
  versionKey: false,
});

'''
