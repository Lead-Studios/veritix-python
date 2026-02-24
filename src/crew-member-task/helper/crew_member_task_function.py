"""Auto-converted from TypeScript.
Original file: crew-member-task/helper/crew-member-task-function.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { BadRequestException, Injectable } from '@nestjs/common';
import { CoordinatesService } from 'src/subscriber-flight-task/coordinates.service';
import { FlightTaskMessages } from 'src/subscriber-flight-task/helper/subscriber-flight-task-messages';
import {
  dateFormat,
  dateTimeFormat,
} from 'src/drone-management/Helper/drone-function';

@Injectable()
export class CrewMemberTaskFunction {
  constructor(private readonly coordinatesService: CoordinatesService) {}
  async getLocationFromCoordinates(
    latitude: number,
    longitude: number,
  ): Promise<string> {
    const result =
      await this.coordinatesService.retrieveLocationFromCoordinates({
        latitude,
        longitude,
      });

    const locationName: string = result.locationName ?? 'Unknown location';

    return locationName;
  }

  public parseTaskTime(flightTime: string): {
    hour: number;
    minute: number;
  } {
    const cleanedTime = flightTime.trim().replace(/\s+/g, ' ');
    const [time, modifierRaw] = cleanedTime.split(' ');

    if (!modifierRaw) {
      throw new BadRequestException(
        FlightTaskMessages.INVALID_FLIGHT_TIME_FORMAT,
      );
    }

    const modifier = modifierRaw.toUpperCase();
    const [hourStr, minuteStr] = time.split(':');
    let hour = Number(hourStr);
    const minute = Number(minuteStr);

    if (modifier === 'PM' && hour !== 12) hour += 12;
    if (modifier === 'AM' && hour === 12) hour = 0;

    return { hour, minute };
  }

  public computeTaskDateTime(
    flightDate: string,
    hour: number,
    minute: number,
  ): Date {
    return new Date(
      `${flightDate}T${hour.toString().padStart(2, '0')}:${minute
        .toString()
        .padStart(2, '0')}:00+01:00`,
    );
  }

  public formatRelativeTime(date: Date | string | null | undefined): string {
    if (!date) return '';

    const targetDate = date instanceof Date ? date : new Date(date);
    if (isNaN(targetDate.getTime())) return '';

    const now = new Date();
    const diffInMs = now.getTime() - targetDate.getTime();
    const diffInSeconds = Math.floor(diffInMs / 1000);
    const diffInMinutes = Math.floor(diffInSeconds / 60);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);
    const diffInWeeks = Math.floor(diffInDays / 7);
    const diffInMonths = Math.floor(diffInDays / 30);
    const diffInYears = Math.floor(diffInDays / 365);

    if (diffInSeconds < 60) {
      return diffInSeconds <= 1 ? 'just now' : `${diffInSeconds} seconds ago`;
    } else if (diffInMinutes < 60) {
      return diffInMinutes === 1
        ? '1 minute ago'
        : `${diffInMinutes} minutes ago`;
    } else if (diffInHours < 24) {
      return diffInHours === 1 ? '1 hour ago' : `${diffInHours} hours ago`;
    } else if (diffInDays < 7) {
      return diffInDays === 1 ? '1 day ago' : `${diffInDays} days ago`;
    } else if (diffInWeeks < 4) {
      return diffInWeeks === 1 ? '1 week ago' : `${diffInWeeks} weeks ago`;
    } else if (diffInMonths < 12) {
      return diffInMonths === 1 ? '1 month ago' : `${diffInMonths} months ago`;
    } else {
      return diffInYears === 1 ? '1 year ago' : `${diffInYears} years ago`;
    }
  }

  public formatDate(input?: Date | string): string {
    return dateFormat(input);
  }

  public formatDateTime(input?: Date | string): string {
    return dateTimeFormat(input);
  }

  public calculateTimeOnSite(
    begunAt: Date | string | null | undefined,
    completedAt: Date | string | null | undefined,
    stoppedAt: Date | string | null | undefined,
  ): string {
    if (!begunAt) return '';

    const startTime = begunAt instanceof Date ? begunAt : new Date(begunAt);
    const endTime = completedAt
      ? completedAt instanceof Date
        ? completedAt
        : new Date(completedAt)
      : stoppedAt
        ? stoppedAt instanceof Date
          ? stoppedAt
          : new Date(stoppedAt)
        : null;

    if (!endTime) return '';

    const diffInMs = endTime.getTime() - startTime.getTime();
    const diffInMinutes = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInDays > 0) {
      return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ${diffInHours % 24} hour${diffInHours % 24 !== 1 ? 's' : ''}`;
    } else if (diffInHours > 0) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ${diffInMinutes % 60} minute${diffInMinutes % 60 !== 1 ? 's' : ''}`;
    } else {
      return `${diffInMinutes} minute${diffInMinutes !== 1 ? 's' : ''}`;
    }
  }
}

'''
