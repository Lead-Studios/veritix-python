"""Auto-converted from TypeScript.
Original file: task-incident/task-incident-interface.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { IncidentStatus } from 'src/common/enum/incident-status';

export interface IncidentCountItem {
  _id: string;
  count: number;
}

export interface IncidentFormat {
  incidentId: string;
  taskId: string;
  severityLevel: string;
  confidenceScore: number;
  wasteType: string;
  createdAt: string;
  gpsCoordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface Task {
  taskId: string;
  location?: string;
  locationCoordinates?: {
    type: string;
    coordinates: [number, number];
  };
}

export interface TaskImage {
  imageUrl: string;
  taskId: string;
}

export interface IncidentResponse {
  taskId: string;
  incidentId: string;
  date: string;
  severity: string;
  confidenceLevel: number;
  incidentType: string;
  location: string;
  locationCoordinates: {
    latitude: number;
    longitude: number;
  };
  imageUrl: string;
}

export interface IncidentProjection {
  incidentId: string;
  wasteType: string;
  status: IncidentStatus;
  imageId: number;
  taskId: string;
}

export interface TaskProjection {
  taskId: string;
  location: string;
  area: string;
}

export interface SubscriberIncidentResponse {
  incidentId: string;
  wasteType: string;
  status: IncidentStatus;
  assignedCrew: string;
  location: string | null;
  area: string | null;
}

'''
