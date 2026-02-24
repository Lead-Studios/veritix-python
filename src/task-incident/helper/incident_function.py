"""Auto-converted from TypeScript.
Original file: task-incident/helper/incident-function.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Injectable } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  IncidentCounter,
  IncidentCounterDocument,
} from '../model/incident-counter';
import {
  IncidentFormat,
  IncidentProjection,
  IncidentResponse,
  SubscriberIncidentResponse,
  Task,
  TaskImage,
  TaskProjection,
} from '../task-incident-interface';
import { IncidentStatus } from 'src/common/enum/incident-status';

@Injectable()
export class IncidentFunction {
  constructor(
    @InjectModel(IncidentCounter.name)
    private incidentCounterModel: Model<IncidentCounterDocument>,
  ) {}

  public async getNextSequence(key: string): Promise<number> {
    await this.incidentCounterModel.updateOne(
      { key },
      { $setOnInsert: { key, value: 0 } },
      { upsert: true },
    );

    const updated = await this.incidentCounterModel.findOneAndUpdate(
      { key },
      { $inc: { value: 1 } },
      { new: true },
    );

    if (!updated) {
      throw new Error(`Failed to increment counter for ${key}`);
    }

    return updated.value;
  }

  public async generateIncidentId(location: string): Promise<string> {
    const prefix = location.substring(0, 3).toUpperCase();
    const next = await this.getNextSequence(`INCIDENT_${prefix}`);
    return `INC-${prefix}-${String(next).padStart(3, '0')}`;
  }

  public formatIncidentResponse(
    incident: IncidentFormat,
    task: Task,
    taskImage: TaskImage,
  ): IncidentResponse {
    return {
      taskId: task.taskId,
      incidentId: incident.incidentId,
      date: incident.createdAt,
      severity: incident.severityLevel,
      confidenceLevel: incident.confidenceScore,
      incidentType: incident.wasteType,
      location: task.location || '',
      locationCoordinates: task.locationCoordinates
        ? {
            latitude: task.locationCoordinates.coordinates[1],
            longitude: task.locationCoordinates.coordinates[0],
          }
        : { latitude: 0, longitude: 0 },
      imageUrl: taskImage.imageUrl || '',
    };
  }

  public formatAllIncidentResponse(
    incident: IncidentProjection,
    task: TaskProjection | undefined,
    imageToCrewMap: Map<number, number>,
    crewMemberMap: Map<number, string>,
  ): SubscriberIncidentResponse {
    let assignedCrew = 'Unassigned';

    if (
      incident.status === IncidentStatus.ASSIGNED_CREW_MEMBER &&
      imageToCrewMap.has(incident.imageId)
    ) {
      const crewId = imageToCrewMap.get(incident.imageId)!;
      assignedCrew = crewMemberMap.get(crewId) ?? 'Unassigned';
    }

    return {
      incidentId: incident.incidentId,
      wasteType: incident.wasteType,
      status: incident.status,
      assignedCrew,
      location: task?.location ?? null,
      area: task?.area ?? null,
    };
  }
}

'''
