"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-location.service.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Injectable, BadRequestException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  CrewMemberLocation,
  CrewMemberLocationDocument,
} from './model/crew-member-location';
import { CrewMemberTask } from './model/crew-member-task';
import { CrewMemberLocationUpdate } from './interface/location-update.interface';
import { CrewMemberTaskMessage } from './helper/crew-member-task-message';

export interface LocationUpdateInput {
  crewMemberId: number;
  taskId: string;
  subscriberId: number;
  latitude: number;
  longitude: number;
  accuracy?: number;
  altitude?: number;
  speed?: number;
  heading?: number;
}

@Injectable()
export class CrewMemberLocationService {
  constructor(
    @InjectModel(CrewMemberLocation.name)
    private locationModel: Model<CrewMemberLocationDocument>,
    @InjectModel(CrewMemberTask.name)
    private taskModel: Model<any>,
  ) {}

  /**
   * Calculate distance between two coordinates using Haversine formula (meters)
   */
  private calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number,
  ): number {
    const R = 6371000;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  async updateLocation(
    input: LocationUpdateInput,
  ): Promise<CrewMemberLocationUpdate | null> {
    try {
      const task = await this.taskModel.findOne({
        taskId: input.taskId,
        crewMemberId: input.crewMemberId,
      });

      if (!task) {
        throw new BadRequestException(
          CrewMemberTaskMessage.TASK_NOT_FOUND_OR_NOT_ASSIGNED,
        );
      }

      const location = await this.locationModel.findOneAndUpdate(
        {
          crewMemberId: input.crewMemberId,
          taskId: input.taskId,
        },
        {
          crewMemberId: input.crewMemberId,
          taskId: input.taskId,
          subscriberId: input.subscriberId,
          latitude: input.latitude,
          longitude: input.longitude,
          accuracy: input.accuracy,
          altitude: input.altitude,
          speed: input.speed,
          heading: input.heading,
          isActive: true,
          lastUpdatedAt: new Date(),
        },
        {
          upsert: true,
          new: true,
          lean: true,
        },
      );

      if (!location) {
        return null;
      }

      const distance = this.calculateDistance(
        input.latitude,
        input.longitude,
        task.gpsCoordinates?.latitude || 0,
        task.gpsCoordinates?.longitude || 0,
      );

      return {
        crewMemberId: location.crewMemberId,
        taskId: location.taskId,
        currentLocation: {
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          altitude: location.altitude,
          speed: location.speed,
          heading: location.heading,
          timestamp: location.lastUpdatedAt,
        },
        taskDestination: {
          latitude: task.gpsCoordinates?.latitude || 0,
          longitude: task.gpsCoordinates?.longitude || 0,
          taskId: task.taskId,
          location: task.location || 'Task Location',
        },
        isActive: location.isActive,
        distance: Math.round(distance),
      };
    } catch (error) {
      console.error('Error updating location:', error);
      return null;
    }
  }

  async markLocationInactive(
    crewMemberId: number,
    taskId: string,
  ): Promise<void> {
    try {
      await this.locationModel.findOneAndUpdate(
        {
          crewMemberId,
          taskId,
        },
        {
          isActive: false,
          lastUpdatedAt: new Date(),
        },
      );
    } catch (error) {
      console.error('Error marking location inactive:', error);
    }
  }

  async hasLocationForTask(
    crewMemberId: number,
    taskId: string,
  ): Promise<boolean> {
    try {
      const location = await this.locationModel.findOne({
        crewMemberId,
        taskId,
      });
      return !!location;
    } catch (error) {
      console.error('Error checking location existence:', error);
      return false;
    }
  }

  async getTaskNavigation(
    crewMemberId: number,
    taskId: string,
  ): Promise<CrewMemberLocationUpdate | null> {
    try {
      const location = (await this.locationModel
        .findOne({
          crewMemberId,
          taskId,
        })
        .lean()) as unknown as CrewMemberLocationDocument | null;

      const task = await this.taskModel.findOne({
        taskId,
        crewMemberId,
      });

      if (!task) {
        return null;
      }

      if (!location) {
        return {
          crewMemberId,
          taskId,
          currentLocation: {
            latitude: 0,
            longitude: 0,
            accuracy: undefined,
            altitude: undefined,
            speed: undefined,
            heading: undefined,
            timestamp: new Date(),
          },
          taskDestination: {
            latitude: task.gpsCoordinates?.latitude || 0,
            longitude: task.gpsCoordinates?.longitude || 0,
            taskId: task.taskId,
            location: task.location || 'Task Location',
          },
          isActive: false,
          distance: undefined,
        };
      }

      const distance = this.calculateDistance(
        location.latitude,
        location.longitude,
        task.gpsCoordinates?.latitude || 0,
        task.gpsCoordinates?.longitude || 0,
      );

      return {
        crewMemberId: location.crewMemberId,
        taskId: location.taskId,
        currentLocation: {
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          altitude: location.altitude,
          speed: location.speed,
          heading: location.heading,
          timestamp: location.lastUpdatedAt,
        },
        taskDestination: {
          latitude: task.gpsCoordinates?.latitude || 0,
          longitude: task.gpsCoordinates?.longitude || 0,
          taskId: task.taskId,
          location: task.location || 'Task Location',
        },
        isActive: location.isActive,
        distance: Math.round(distance),
      };
    } catch (error) {
      console.error('Error fetching task navigation:', error);
      return null;
    }
  }

  async deleteLocationForTask(
    crewMemberId: number,
    taskId: string,
  ): Promise<void> {
    try {
      await this.locationModel.findOneAndDelete({
        crewMemberId,
        taskId,
      });
      console.log(
        `Location deleted for crew member ${crewMemberId}, task ${taskId}`,
      );
    } catch (error) {
      console.error('Error deleting location:', error);
    }
  }
}

'''
