"""Auto-converted from TypeScript.
Original file: drone-management/Helper/drone-function.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  DroneMissionHistoryItem,
  FormattableDrone,
  TaskMissionInput,
} from '../interface/drone-interface';

export function formatDroneResponse(drone: FormattableDrone) {
  return {
    _id: drone._id,
    droneId: drone.droneId,
    droneMake: drone.droneMake,
    operatorName: drone.pilotInfo
      ? `${drone.pilotInfo.firstName} ${drone.pilotInfo.lastName}`
      : null,
    status: drone.status,
    isFlag: drone.isFlag ?? false,
    isGrounded: drone.isGrounded ?? false,
    numberOfActiveFlights: drone.numberOfActiveFlights ?? 0,
    totalFlightHours: drone.totalFlightHours ?? 0,
    createdAt: dateFormat(drone.createdAt),
  };
}
export function dateFormat(input?: Date | string): string {
  if (!input) return '';

  const date = input instanceof Date ? input : new Date(input);

  if (isNaN(date.getTime())) return '';

  const day = date.getDate();
  const month = date.toLocaleString('en-US', { month: 'long' });
  const year = date.getFullYear();

  const suffix =
    day % 10 === 1 && day !== 11
      ? 'st'
      : day % 10 === 2 && day !== 12
        ? 'nd'
        : day % 10 === 3 && day !== 13
          ? 'rd'
          : 'th';

  return `${day}${suffix} ${month} ${year}`;
}

export function dateTimeFormat(input?: Date | string): string {
  if (!input) return '';

  const date = input instanceof Date ? input : new Date(input);

  if (isNaN(date.getTime())) return '';

  const day = date.getDate();
  const month = date.toLocaleString('en-US', { month: 'long' });
  const year = date.getFullYear();
  const time = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });

  const suffix =
    day % 10 === 1 && day !== 11
      ? 'st'
      : day % 10 === 2 && day !== 12
        ? 'nd'
        : day % 10 === 3 && day !== 13
          ? 'rd'
          : 'th';

  return `${day}${suffix} ${month} ${year} at ${time}`;
}

export function formatDroneMissionItem(
  droneId: string,
  task: TaskMissionInput,
  incidentCount: number,
  distanceCovered: number,
): DroneMissionHistoryItem {
  const flightDate = new Date(task.flightDateTime);
  const time = new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(flightDate);

  return {
    droneId,
    taskId: task.taskId,
    date: flightDate.toISOString().split('T')[0],
    time,
    area: task.area,
    location: task.location,
    incidentCount,
    distanceCovered,
  };
}

'''
