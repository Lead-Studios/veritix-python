"""Auto-converted from TypeScript.
Original file: drone-management/interface/drone-interface.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Types } from 'mongoose';
import { Drone } from '../model/drone';
import { PaginationMeta } from 'src/common/pagination';

export interface DroneStats {
  totalDrones: number;
  activeDrones: number;
  underMaintenanceDrones: number;
  totalDistanceCovered: number;
}
export interface TotalDistanceResult {
  totalDistance: number;
}

export type DroneWithPilotInfo = Drone & {
  pilotInfo?: {
    onboardingId: number;
    firstName: string;
    lastName: string;
    email: string;
    phoneNumber: string;
    customerId: string;
  };
  distanceCovered: number;
  numberOfActiveFlights: number;
  totalFlightHours: number;
  areas: string[];
};

export interface FormattableDrone {
  _id: Types.ObjectId | string;
  droneId: string;
  droneMake: string;
  pilotInfo?: {
    firstName: string;
    lastName: string;
  };
  status: string;
  isFlag: boolean;
  isGrounded: boolean;
  numberOfActiveFlights?: number;
  totalFlightHours?: number;
  createdAt?: Date;
}

export interface FlagHistoryItem {
  droneId: string;
  droneOwner: {
    firstName: string;
    lastName: string;
    email: string;
    customerId: string;
  };
  droneModel: string;
  droneMake: string;
  dateFlagged: string;
}

export interface GetFlagHistoryResponse {
  message: string;
  data: FlagHistoryItem[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    itemsPerPage: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPrevPage: boolean;
  };
}

export interface GetFlaggedDronesResponse {
  message: string;
  data: any[];
  pagination: PaginationMeta;
}

export interface DroneMissionHistoryItem {
  droneId: string;
  taskId: string;
  date: string;
  time: string;
  area: string;
  location: string;
  incidentCount: number;
  distanceCovered: number;
}

export interface DroneMissionHistoryStats {
  totalCompletedTasks: number;
  totalIncidents: number;
  totalDistanceCovered: number;
}

export interface DroneMissionHistoryResponse {
  message: string;
  stats: {
    totalCompletedTasks: number;
    totalIncidents: number;
    totalDistanceCovered: number;
  };
  missions: DroneMissionHistoryItem[];
  pagination: {
    currentPage: number;
    totalPages: number;
    totalItems: number;
    limit: number;
  };
}

export interface TaskWithFlightDate {
  flightDateTime: string | Date;
}

export interface TaskSummary {
  taskId: string;
  area: string;
  location: string;
}

export type TaskMissionInput = TaskSummary & TaskWithFlightDate;

export interface RetrieveDroneMissionHistoryDto {
  page?: number;
  limit?: number;
  search?: string;
}

'''
