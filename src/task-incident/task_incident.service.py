"""Auto-converted from TypeScript.
Original file: task-incident/task-incident.service.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { CreateTaskIncidentDto } from './dto/create-task-incident.dto';
import { Incident, IncidentDocument } from './model/incident';
import { TaskImage, TaskImageDocument } from './model/task-image';
import { IncidentFunction } from './helper/incident-function';
import {
  PilotTaskFlight,
  PilotTaskFlightDocument,
} from 'src/pilot-flight-task/model/pilot-flight-task';
import { IncidentMessage } from './helper/incident-messages';
import { IncidentStatus } from 'src/common/enum/incident-status';
import { PaginationHelper } from 'src/common/pagination';
import {
  IncidentFormat,
  IncidentProjection,
  IncidentResponse,
  SubscriberIncidentResponse,
  TaskProjection,
} from './task-incident-interface';
import {
  SubscriberFlightTask,
  SubscriberFlightTaskDocument,
} from 'src/subscriber-flight-task/model/subscriber-flight-task';
import { dateFormat } from 'src/drone-management/Helper/drone-function';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';
import {
  CrewMemberTask,
  CrewMemberTaskDocument,
} from 'src/crew-member-task/model/crew-member-task';
import {
  CrewMember,
  CrewMemberDocument,
} from 'src/crew-member-management/model/crew-member';
import { CrewMemberTaskMessage } from 'src/crew-member-task/helper/crew-member-task-message';
import { User, UserDocument } from 'src/user-auth/model/user';
import { IncidentEmailFunctions } from './helper/incident-email-function';
import { UserMessages } from 'src/user-auth/helper/user-messages';
import { FlightTaskMessages } from 'src/subscriber-flight-task/helper/subscriber-flight-task-messages';

@Injectable()
export class TaskIncidentService {
  constructor(
    @InjectModel(Incident.name)
    private readonly taskIncidentModel: Model<IncidentDocument>,
    @InjectModel(TaskImage.name)
    private readonly taskImageModel: Model<TaskImageDocument>,
    @InjectModel(PilotTaskFlight.name)
    private readonly pilotTaskFlightModel: Model<PilotTaskFlightDocument>,
    @InjectModel(SubscriberFlightTask.name)
    private readonly subscriberFlightTaskModel: Model<SubscriberFlightTaskDocument>,
    @InjectModel(CrewMemberTask.name)
    private readonly crewMemberTaskModel: Model<CrewMemberTaskDocument>,
    @InjectModel(CrewMember.name)
    private readonly crewMemberModel: Model<CrewMemberDocument>,
    @InjectModel(User.name)
    private readonly userModel: Model<UserDocument>,
    private readonly incidentFunction: IncidentFunction,
    private readonly incidentEmailFunctions: IncidentEmailFunctions,
  ) {}

  async createTaskIncident(
    dto: CreateTaskIncidentDto | CreateTaskIncidentDto[],
  ): Promise<{ taskImages: TaskImage[]; incidents: Incident[] }> {
    const dtos = Array.isArray(dto) ? dto : [dto];
    const taskImages: TaskImage[] = [];
    const allIncidents: Incident[] = [];

    if (dtos.length === 0) {
      return { taskImages, incidents: allIncidents };
    }

    const taskFlight = await this.pilotTaskFlightModel.findOne({
      taskId: dtos[0].taskId,
    });

    if (!taskFlight) {
      throw new NotFoundException(IncidentMessage.FLIGHT_TASK_FOUND);
    }

    const pilotId = taskFlight.acceptedBy ?? taskFlight.pilot?.[0];
    if (!pilotId) {
      throw new NotFoundException(IncidentMessage.NO_PILOT_ASSIGNED);
    }

    const subscriberFlight = await this.subscriberFlightTaskModel.findOne({
      taskId: dtos[0].taskId,
    });

    if (!subscriberFlight) {
      throw new NotFoundException(IncidentMessage.FLIGHT_TASK_FOUND);
    }

    const subscriberId = subscriberFlight.createdBy;
    if (!subscriberId) {
      throw new NotFoundException(IncidentMessage.NO_SUBSCRIBER_ASSIGNED);
    }

    for (const imageDto of dtos) {
      let taskImage = await this.taskImageModel.findOne({
        taskId: imageDto.taskId,
        filename: imageDto.imageMetadata.filename,
      });

      if (!taskImage) {
        taskImage = new this.taskImageModel({
          taskId: imageDto.taskId,
          pilotId,
          subscriberId,
          filename: imageDto.imageMetadata.filename,
          s3Bucket: imageDto.imageMetadata.s3_bucket,
          s3Key: imageDto.imageMetadata.s3_filename,
          imageUrl: imageDto.imageMetadata.imageUrl,
          captureTimestamp: new Date(imageDto.imageMetadata.capture_timestamp),
          imageWidth: imageDto.imageMetadata.image_width,
          imageHeight: imageDto.imageMetadata.image_height,
          totalIncidents: 0,
          totalWasteAreaSqm: 0,
        });

        await taskImage.save();
      }

      const incidentsData = await Promise.all(
        imageDto.detections.map(async (detection) => ({
          incidentId: await this.incidentFunction.generateIncidentId(
            taskFlight.location,
          ),
          taskId: imageDto.taskId,
          pilotId,
          subscriberId,
          imageId: taskImage.imageId,
          wasteType: detection.waste_type,
          severityLevel: imageDto.severityLevel,
          confidenceScore: detection.confidence_score,
          processingDurationMs: imageDto.processingDurationMs,
          areaPixels: detection.area_pixels,
          areaSquareMeters: detection.area_square_meters,
          boundingBox: {
            xMin: detection.bounding_box.x_min,
            yMin: detection.bounding_box.y_min,
            xMax: detection.bounding_box.x_max,
            yMax: detection.bounding_box.y_max,
            width: detection.bounding_box.width,
            height: detection.bounding_box.height,
          },
          gpsCoordinates: {
            latitude: detection.gps_coordinates.latitude,
            longitude: detection.gps_coordinates.longitude,
            altitude: detection.gps_coordinates.altitude,
            accuracy: detection.gps_coordinates.accuracy,
          },
          modelVersion: imageDto.modelVersion,
          MLRunStatus: imageDto.status,
          status: IncidentStatus.PENDING,
        })),
      );

      const incidentDocs =
        await this.taskIncidentModel.insertMany(incidentsData);

      const incidents = incidentDocs.map((doc) => doc.toObject() as Incident);

      const totalWasteAreaSqm = incidents.reduce(
        (sum, inc) => sum + inc.areaSquareMeters,
        0,
      );

      taskImage.totalIncidents += incidents.length;
      taskImage.totalWasteAreaSqm += totalWasteAreaSqm;
      await taskImage.save();

      taskImages.push(taskImage);
      allIncidents.push(...incidents);
    }

    return { taskImages, incidents: allIncidents };
  }

  async notifyTaskIncidentsComplete(
    taskId: string,
  ): Promise<{ message: string; emailSent: boolean }> {
    const subscriberTask =
      await this.subscriberFlightTaskModel.findOneAndUpdate(
        { taskId },
        { $set: { status: FlightTaskStatus.PROCESSING } },
        { new: true },
      );

    if (!subscriberTask) {
      throw new NotFoundException(
        CrewMemberTaskMessage.SUBSCRIBER_TASK_NOT_FOUND,
      );
    }

    const allIncidents = await this.taskIncidentModel.find({ taskId }).lean();

    const subscriberUser = await this.userModel.findOne({
      userId: subscriberTask.createdBy,
    });

    if (!subscriberUser) {
      throw new NotFoundException(UserMessages.USER_NOT_FOUND);
    }

    const organizationName = `${subscriberUser.firstName} ${subscriberUser.lastName}`;

    const severityMap = allIncidents.reduce(
      (acc, incident) => {
        acc[incident.severityLevel] = (acc[incident.severityLevel] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    );
    const severitySummary = Object.entries(severityMap)
      .map(([severity, count]) => `${severity}: ${count}`)
      .join(', ');
    const taskUrl = `${process.env.SUBSCRIBER_INCIDENT_RESULT_URL}/${subscriberTask.taskId}`;

    await this.incidentEmailFunctions.sendIncidentResultReadyEmail({
      to: subscriberUser.email,
      organizationName,
      taskId: subscriberTask.taskId,
      totalIncidents: allIncidents.length,
      severitySummary,
      taskUrl,
    });

    return {
      message: 'Subscriber notified successfully',
      emailSent: true,
    };
  }

  async retrieveTaskImagesBySubscriberTask(
    taskId: string,
    options: { page?: number; limit?: number } = {},
  ) {
    const { page = 1, limit = 50 } = options;

    const { skip, limit: take } = PaginationHelper.parsePagination({
      page,
      limit,
    });

    /**
     * FILTER:
     * - Only PENDING images
     * - Only images with incidents > 0
     */
    const filter = {
      taskId,
      status: FlightTaskStatus.PENDING,
      totalIncidents: { $gt: 0 }, // 🔥 IMPORTANT CHANGE
    };

    const totalItems = await this.taskImageModel.countDocuments(filter);

    const images = await this.taskImageModel
      .find(filter)
      .select('imageId imageUrl -_id')
      .sort({ imageId: 1 })
      .skip(skip)
      .limit(take)
      .lean();

    /**
     * Aggregate total incidents ONLY for images > 0
     */
    const incidentAggregation = await this.taskImageModel.aggregate<{
      _id: null;
      totalIncidents: number;
    }>([
      { $match: filter },
      {
        $group: {
          _id: null,
          totalIncidents: { $sum: '$totalIncidents' },
        },
      },
    ]);

    const totalIncidents =
      incidentAggregation.length > 0
        ? incidentAggregation[0].totalIncidents
        : 0;

    const subscriberTask = await this.subscriberFlightTaskModel
      .findOne({ taskId })
      .select('status area location startPosition endPosition -_id')
      .lean();

    if (!subscriberTask) {
      throw new NotFoundException(IncidentMessage.FLIGHT_TASK_FOUND);
    }

    const taskArea = subscriberTask.area;
    const taskLocation = subscriberTask.location;

    const coordinates = {
      startPosition: subscriberTask?.startPosition?.coordinates
        ? {
            longitude: subscriberTask.startPosition.coordinates[0],
            latitude: subscriberTask.startPosition.coordinates[1],
          }
        : null,

      endPosition: subscriberTask?.endPosition?.coordinates
        ? {
            longitude: subscriberTask.endPosition.coordinates[0],
            latitude: subscriberTask.endPosition.coordinates[1],
          }
        : null,
    };

    const subscriberTaskStatus = subscriberTask?.status ?? 'UNKNOWN';

    const crewMemberTask = await this.crewMemberTaskModel
      .findOne({ taskId })
      .select('status -_id')
      .lean();

    const paginatedResponse = PaginationHelper.createPaginatedResponse(
      images,
      totalItems,
      { page, limit },
      undefined,
      totalItems === 0
        ? FlightTaskMessages.FLIGHT_TASK_NOT_FOUND
        : IncidentMessage.TASK_IMAGE_RETRIEVED,
    );

    const { message, data, pagination } = paginatedResponse;

    return {
      message,
      data,
      totalIncidents,
      subscriberTaskStatus,
      taskArea,
      taskLocation,
      coordinates,
      crewMemberTaskStatus: crewMemberTask?.status ?? null,
      pagination,
    };
  }

  public async retrieveIncidentsByImage(
    imageId: number,
  ): Promise<{ message: string; data: IncidentResponse[] }> {
    const taskImage = await this.taskImageModel.findOne({
      imageId,
    });

    if (!taskImage) {
      throw new NotFoundException(IncidentMessage.TASK_IMAGE_NOT_FOUND);
    }

    const incidentsFromDb = await this.taskIncidentModel
      .find({ imageId: taskImage.imageId })
      .lean()
      .exec();

    const responses: IncidentResponse[] = [];

    for (const incidentDoc of incidentsFromDb) {
      const incident: IncidentFormat = {
        incidentId: incidentDoc.incidentId,
        taskId: incidentDoc.taskId,
        severityLevel: incidentDoc.severityLevel,
        confidenceScore: incidentDoc.confidenceScore,
        wasteType: incidentDoc.wasteType,
        createdAt: dateFormat(incidentDoc.createdAt),
      };

      const task = await this.subscriberFlightTaskModel.findOne({
        taskId: incident.taskId,
      });

      if (!task) {
        return {
          message: IncidentMessage.INCIDENTS_RETRIEVED_SUCCESSFULLY,
          data: [],
        };
      }

      responses.push(
        this.incidentFunction.formatIncidentResponse(incident, task, taskImage),
      );
    }

    return {
      message: IncidentMessage.INCIDENTS_RETRIEVED_SUCCESSFULLY,
      data: responses,
    };
  }

  async retrieveAllSubscriberIncidents(
    subscriberId: number,
    options: {
      page?: number;
      limit?: number;
      search?: string;
      status?: IncidentStatus;
    } = {},
  ): Promise<
    ReturnType<
      typeof PaginationHelper.createPaginatedResponse<SubscriberIncidentResponse>
    >
  > {
    const { page = 1, limit = 10, search, status } = options;

    const { skip, limit: take } = PaginationHelper.parsePagination({
      page,
      limit,
    });

    const filter: Record<string, any> = { subscriberId };

    if (search) {
      filter.incidentId = { $regex: search, $options: 'i' };
    }

    if (status) {
      filter.status = status;
    }

    const totalItems = await this.taskIncidentModel.countDocuments(filter);

    const incidents = await this.taskIncidentModel
      .find(filter)
      .select('incidentId wasteType status imageId taskId')
      .skip(skip)
      .limit(take)
      .sort({ createdAt: -1 })
      .lean<IncidentProjection[]>();

    if (!incidents.length) {
      return PaginationHelper.createPaginatedResponse(
        [],
        totalItems,
        { page, limit },
        undefined,
        IncidentMessage.INCIDENT_NOT_FOUND,
      );
    }

    const taskIds = [...new Set(incidents.map((i) => i.taskId))];

    const tasks = await this.subscriberFlightTaskModel
      .find({ taskId: { $in: taskIds } })
      .select('taskId location area')
      .lean<TaskProjection[]>();

    const taskMap = new Map<string, TaskProjection>(
      tasks.map((t) => [t.taskId, t]),
    );

    const imageIds = incidents.map((i) => i.imageId);

    const crewTasks = await this.crewMemberTaskModel
      .find({
        imageAssigned: { $in: imageIds },
        status: FlightTaskStatus.ASSIGNED_CREW_MEMBER,
      })
      .select('crewMemberId imageAssigned')
      .lean<{ crewMemberId: number; imageAssigned: number[] }[]>();

    const imageToCrewMap = new Map<number, number>();
    crewTasks.forEach((task) => {
      task.imageAssigned.forEach((imageId) => {
        imageToCrewMap.set(imageId, task.crewMemberId);
      });
    });

    const crewMemberIds = [...new Set(imageToCrewMap.values())];

    const crewMembers = await this.crewMemberModel
      .find({ crewMemberId: { $in: crewMemberIds } })
      .select('crewMemberId firstName lastName')
      .lean<{ crewMemberId: number; firstName: string; lastName: string }[]>();

    const crewMemberMap = new Map<number, string>();
    crewMembers.forEach((cm) => {
      crewMemberMap.set(cm.crewMemberId, `${cm.firstName} ${cm.lastName}`);
    });

    const formattedResponse = incidents.map((incident) =>
      this.incidentFunction.formatAllIncidentResponse(
        incident,
        taskMap.get(incident.taskId),
        imageToCrewMap,
        crewMemberMap,
      ),
    );

    const message =
      totalItems === 0
        ? IncidentMessage.INCIDENT_NOT_FOUND
        : IncidentMessage.INCIDENTS_RETRIEVED_SUCCESSFULLY;

    return PaginationHelper.createPaginatedResponse(
      formattedResponse,
      totalItems,
      { page, limit },
      undefined,
      message,
    );
  }
}

'''
