"""Auto-converted from TypeScript.
Original file: drone-management/drone-management.service.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
import {
  BadRequestException,
  ConflictException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { CreateDroneDto } from './dto/create-drone.dto';
import { GetDronesDto } from './dto/get-drones.dto';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import {
  PilotOnboarding,
  PilotOnboardingDocument,
} from 'src/pilot-onboarding/model/pilot-onboarding';
import { Drone, DroneDocument } from './model/drone';
import { FileUploadService } from 'src/config/upload/upload.service';
import { DroneStatus } from '../common/enum/drone-status';
import { DroneMessages } from './Helper/drone-messages';
import { Types, Document } from 'mongoose';
import { PaginationHelper } from 'src/common/pagination';
import { PaginatedResponse } from 'src/common/pagination';
import { PilotEmailFunctions } from 'src/pilot-onboarding/Helper/pilot-email-function';
import {
  formatDroneResponse,
  dateFormat,
  formatDroneMissionItem,
} from './Helper/drone-function';
import {
  DroneMissionHistoryResponse,
  DroneMissionHistoryItem,
  RetrieveDroneMissionHistoryDto,
} from './interface/drone-interface';
import {
  PilotDroneFootageDocument,
  PilotDroneFootages,
} from 'src/pilot-drone-footages/model/pilot-drone-footages';
import {
  PilotTaskFlight,
  PilotTaskFlightDocument,
} from 'src/pilot-flight-task/model/pilot-flight-task';
import { Incident, IncidentDocument } from 'src/task-incident/model/incident';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';

@Injectable()
export class DroneService {
  constructor(
    @InjectModel(Drone.name)
    private readonly droneModel: Model<DroneDocument>,
    @InjectModel(PilotOnboarding.name)
    private readonly pilotModel: Model<PilotOnboarding>,
    private readonly fileUploadService: FileUploadService,
    private readonly pilotEmailFunctions: PilotEmailFunctions,
    @InjectModel(PilotTaskFlight.name)
    private readonly pilotTaskModel: Model<PilotTaskFlightDocument>,
    @InjectModel(PilotDroneFootages.name)
    private readonly pilotDroneFootageModel: Model<PilotDroneFootageDocument>,
    @InjectModel(Incident.name)
    private readonly taskIncidentModel: Model<IncidentDocument>,
  ) {}

  async createDrone(
    createPilotDroneDto: CreateDroneDto,
    file?: Express.Multer.File,
  ): Promise<{ message: string }> {
    const { onboardingId, droneSerialNumber, numberOfDrones } =
      createPilotDroneDto;

    const pilot = await this.pilotModel.findOne({ onboardingId });
    if (!pilot) {
      throw new NotFoundException(DroneMessages.PILOT_NOT_FOUND);
    }

    const existingDrone = await this.droneModel.findOne({
      droneSerialNumber,
    });
    if (existingDrone) {
      throw new ConflictException(DroneMessages.DRONE_ALREADY_REGISTERED);
    }

    let ncaaCertificationUrl: string | undefined;

    if (file) {
      ncaaCertificationUrl =
        await this.fileUploadService.handleFileUpload(file);
    }
    const newDrone = new this.droneModel({
      ...createPilotDroneDto,
      ncaaCertificationImage: ncaaCertificationUrl,
      pilot: onboardingId,
      status: DroneStatus.IN_REVIEW,
    });

    try {
      await newDrone.save();

      if (typeof numberOfDrones === 'number') {
        pilot.numberOfDrones = numberOfDrones;
        await pilot.save();
      }

      try {
        await this.pilotEmailFunctions.sendPilotOnboardingEmail(
          pilot.email,
          pilot.firstName,
        );
      } catch (emailError) {
        console.error('Error sending emails:', emailError);
      }

      return {
        message: DroneMessages.DRONE_CREATED_SUCCESSFULLY,
      };
    } catch (error) {
      throw new BadRequestException(`Failed to create drone: ${error}`);
    }
  }

  async getAllDrones(filters: GetDronesDto = {}): Promise<
    PaginatedResponse<any> & {
      stats: {
        totalDrones: number;
        activeDrones: number;
        underMaintenanceDrones: number;
        totalDistanceCovered: number;
      };
    }
  > {
    const { search, status, pilotId, droneMake, droneModel, page, limit } =
      filters;

    const baseQuery: Record<string, any> = {};

    if (status) {
      baseQuery.status = status;
    }

    if (pilotId !== undefined && pilotId !== null) {
      const pilotIdNum = Number(pilotId);
      if (!isNaN(pilotIdNum) && pilotIdNum > 0) {
        baseQuery.pilot = pilotIdNum;
      }
    }

    if (droneMake && droneMake.trim() !== '') {
      baseQuery.droneMake = { $regex: droneMake.trim(), $options: 'i' };
    }

    if (droneModel && droneModel.trim() !== '') {
      baseQuery.droneModel = { $regex: droneModel.trim(), $options: 'i' };
    }

    if (search && search.trim() !== '') {
      baseQuery.$or = [
        { droneId: { $regex: search.trim(), $options: 'i' } },
        { droneMake: { $regex: search.trim(), $options: 'i' } },
        { droneModel: { $regex: search.trim(), $options: 'i' } },
        { droneSerialNumber: { $regex: search.trim(), $options: 'i' } },
      ];
    }

    const {
      skip,
      limit: take,
      page: currentPage,
    } = PaginationHelper.parsePagination({
      page: page ? parseInt(String(page), 10) : undefined,
      limit: limit ? parseInt(String(limit), 10) : undefined,
    });

    const [
      totalDrones,
      activeDrones,
      underMaintenanceDrones,
      totalDistanceResult,
    ] = await Promise.all([
      this.droneModel.countDocuments(),
      this.droneModel.countDocuments({ status: DroneStatus.ACTIVE }),
      this.droneModel.countDocuments({ status: DroneStatus.UNDER_MAINTENANCE }),
      this.droneModel.aggregate([
        {
          $group: {
            _id: null,
            totalDistance: { $sum: '$distanceCovered' },
          },
        },
      ]),
    ]);

    const totalDistanceCovered =
      totalDistanceResult.length > 0
        ? totalDistanceResult[0].totalDistance || 0
        : 0;

    const filteredCount = await this.droneModel.countDocuments(baseQuery);

    const drones = await this.droneModel
      .find(baseQuery)
      .skip(skip)
      .limit(take)
      .sort({ createdAt: -1 })
      .lean();

    const pilotIds = [...new Set(drones.map((d) => d.pilot))];

    const pilots = await this.pilotModel
      .find({ onboardingId: { $in: pilotIds } })
      .lean();

    const pilotMap = new Map(
      pilots.map((pilot) => [
        pilot.onboardingId,
        {
          firstName: pilot.firstName,
          lastName: pilot.lastName,
        },
      ]),
    );

    const formattedDrones = drones.map((drone) =>
      formatDroneResponse({
        _id: drone._id as unknown as Types.ObjectId,
        droneId: drone.droneId,
        droneMake: drone.droneMake,
        pilotInfo: pilotMap.get(drone.pilot),
        status: drone.status,
        isFlag: drone.isFlag ?? false,
        isGrounded: drone.isGrounded ?? false,
        numberOfActiveFlights: drone.numberOfActiveFlights ?? 0,
        totalFlightHours: drone.totalFlightHours ?? 0,
        createdAt: drone.createdAt,
      }),
    );

    const response = PaginationHelper.createPaginatedResponse(
      formattedDrones,
      filteredCount,
      { page: currentPage, limit: take },
      totalDrones,
      DroneMessages.DRONES_RETRIEVED_SUCCESSFULLY,
    );

    return {
      ...response,
      pagination: {
        ...response.pagination,
        itemsPerPage: response.pagination.limit,
      },
      stats: {
        totalDrones,
        activeDrones,
        underMaintenanceDrones,
        totalDistanceCovered,
      },
    };
  }

  async getDroneById(droneId: string): Promise<{
    message: string;
    data: any;
  }> {
    const drone = await this.droneModel.findOne({ droneId }).lean();
    if (!drone) {
      throw new NotFoundException(DroneMessages.DRONE_NOT_FOUND);
    }

    const pilot = await this.pilotModel
      .findOne({ onboardingId: drone.pilot })
      .lean<PilotOnboardingDocument | null>();

    const droneWithPilotInfo = {
      ...drone,
      pilotInfo: pilot
        ? {
            onboardingId: pilot.onboardingId,
            firstName: pilot.firstName,
            lastName: pilot.lastName,
            email: pilot.email,
            phoneNumber: pilot.phoneNumber,
            customerId: pilot.customerId,
          }
        : undefined,
      distanceCovered: drone.distanceCovered ?? 0,
      numberOfActiveFlights: drone.numberOfActiveFlights ?? 0,
      totalFlightHours: drone.totalFlightHours ?? 0,
      areas: drone.areas ?? [],
      createdAt: dateFormat(drone.createdAt),
      updatedAt: dateFormat(drone.updatedAt),
      isFlag: drone.isFlag ?? false,
      isGrounded: drone.isGrounded ?? false,
      licenseExpiryDate: dateFormat(drone.licenseExpiryDate),
    };

    return {
      message: DroneMessages.DRONE_RETRIEVED_SUCCESSFULLY,
      data: droneWithPilotInfo,
    };
  }

  async retrieveDroneMissionHistory(
    droneId: string,
    options: RetrieveDroneMissionHistoryDto = {},
  ): Promise<DroneMissionHistoryResponse> {
    const { page = 1, limit = 10, search } = options;

    const drone = await this.droneModel.findOne({ droneId }).lean();
    if (!drone) {
      throw new NotFoundException(DroneMessages.DRONE_NOT_FOUND);
    }

    const { skip, limit: take } = PaginationHelper.parsePagination({
      page,
      limit,
    });

    const filter: Record<string, any> = { droneId };

    if (search && search.trim() !== '') {
      const keyword = search.trim();
      filter.$or = [
        { taskId: { $regex: keyword, $options: 'i' } },
        { area: { $regex: keyword, $options: 'i' } },
        { location: { $regex: keyword, $options: 'i' } },
      ];
    }

    const totalItems = await this.pilotTaskModel.countDocuments(filter);

    if (totalItems === 0) {
      return {
        message: DroneMessages.MISSION_HISTORY_RETRIEVED_SUCCESSFULLY,
        stats: {
          totalCompletedTasks: 0,
          totalIncidents: 0,
          totalDistanceCovered: 0,
        },
        missions: [],
        pagination: {
          currentPage: page,
          limit,
          totalItems: 0,
          totalPages: 0,
        },
      };
    }

    const pilotTasks = await this.pilotTaskModel
      .find(filter)
      .skip(skip)
      .limit(take)
      .sort({ flightDateTime: -1 })
      .lean();

    const allTasks = await this.pilotTaskModel
      .find({ droneId })
      .select('status taskId')
      .lean();

    let totalCompletedTasks = 0;
    let totalIncidents = 0;
    let totalDistanceCovered = 0;

    for (const task of allTasks) {
      if (task.status === FlightTaskStatus.COMPLETED) {
        totalCompletedTasks += 1;
      }

      totalIncidents += await this.taskIncidentModel.countDocuments({
        taskId: task.taskId,
      });

      const footages = await this.pilotDroneFootageModel
        .find({ taskId: task.taskId })
        .select('distanceCovered')
        .lean();

      totalDistanceCovered += footages.reduce(
        (sum, f) => sum + (f.distanceCovered || 0),
        0,
      );
    }

    const missions: DroneMissionHistoryItem[] = [];

    for (const task of pilotTasks) {
      const footages = await this.pilotDroneFootageModel
        .find({ taskId: task.taskId })
        .select('distanceCovered')
        .lean();

      const distanceCovered = footages.reduce(
        (sum, f) => sum + (f.distanceCovered || 0),
        0,
      );

      const incidentCount = await this.taskIncidentModel.countDocuments({
        taskId: task.taskId,
      });

      missions.push(
        formatDroneMissionItem(droneId, task, incidentCount, distanceCovered),
      );
    }

    const paginatedResponse = PaginationHelper.createPaginatedResponse(
      missions,
      totalItems,
      { page, limit },
    );

    return {
      message: DroneMessages.MISSION_HISTORY_RETRIEVED_SUCCESSFULLY,
      stats: {
        totalCompletedTasks,
        totalIncidents,
        totalDistanceCovered,
      },
      missions: paginatedResponse.data,
      pagination: paginatedResponse.pagination,
    };
  }
}

'''
