"""Auto-converted from TypeScript.
Original file: task-incident/model/task-image.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types } from 'mongoose';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';

export type TaskImageDocument = TaskImage & Document;

@Schema({ timestamps: true })
export class TaskImage {
  @Prop({ unique: true })
  imageId: number;

  @Prop({ required: true, ref: 'SubscriberFlightTask' })
  taskId: string;

  @Prop({ type: Number, ref: 'User', required: true })
  pilotId: number;

  @Prop({ required: true })
  filename: string;

  @Prop({ required: true })
  s3Bucket: string;

  @Prop({ required: true })
  s3Key: string;

  @Prop({ required: true })
  imageUrl: string;

  @Prop({ required: true })
  captureTimestamp: Date;

  @Prop({ required: true })
  imageWidth: number;

  @Prop({ required: true })
  imageHeight: number;

  @Prop({ default: 0 })
  totalIncidents: number;

  @Prop({ type: Number, ref: 'User', required: true })
  subscriberId: number;

  @Prop({ default: 0 })
  totalWasteAreaSqm: number;
  @Prop({
    type: String,
    enum: FlightTaskStatus,
    default: FlightTaskStatus.PENDING,
  })
  status: FlightTaskStatus;
}

export const TaskImageSchema = SchemaFactory.createForClass(TaskImage);

TaskImageSchema.index({ taskId: 1 });
TaskImageSchema.index({ pilotId: 1 });

TaskImageSchema.pre<TaskImageDocument>('validate', async function (next) {
  if (this.isNew && !this.imageId) {
    const lastImage = await this.model('TaskImage')
      .findOne({}, { imageId: 1 })
      .sort({ imageId: -1 })
      .lean<{ imageId: number }>();

    this.imageId = lastImage?.imageId ? lastImage.imageId + 1 : 1;
  }
  next();
});

TaskImageSchema.virtual('incidents', {
  ref: 'Incident',
  localField: 'imageId',
  foreignField: 'imageId',
});

TaskImageSchema.set('toJSON', {
  virtuals: true,
  versionKey: false,
  transform: (_doc, ret) => {
    const r = ret as Partial<TaskImage> & {
      id?: string;
      _id?: Types.ObjectId;
      __v?: number;
    };

    if (r._id) {
      r.id = r._id.toString();
      delete r._id;
    }

    delete r.__v;

    return r;
  },
});

TaskImageSchema.set('toObject', {
  virtuals: true,
});

'''
