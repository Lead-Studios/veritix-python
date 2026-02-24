"""Auto-converted from TypeScript.
Original file: crew-member-task/interface/location-update.interface.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
export interface GpsCoordinates {
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number;
  speed?: number;
  heading?: number;
}

export interface TaskDestination {
  latitude: number;
  longitude: number;
  taskId: string;
  location: string;
}

export interface CrewMemberLocationUpdate {
  crewMemberId: number;
  taskId: string;
  currentLocation: GpsCoordinates & { timestamp: Date };
  taskDestination: TaskDestination;
  isActive: boolean;
  distance?: number;
}

'''
