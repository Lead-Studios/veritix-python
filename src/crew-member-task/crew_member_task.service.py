"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-task.service.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  BadRequestException,
  Injectable,
  NotFoundException,
} from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';
import { Incident, IncidentDocument } from 'src/task-incident/model/incident';
import {
  TaskImage,
  TaskImageDocument,
} from 'src/task-incident/model/task-image';
import { AssignCrewMemberTaskDto } from './dto/assign-crew-member-task.dto';
import { GetCrewMemberTasksDto } from './dto/get-crew-member-tasks.dto';
import { RejectCrewMemberTaskDto } from './dto/reject-crew-member-task.dto';
import { StopCrewMemberTaskDto } from './dto/stop-crew-member-task.dto';
import { CompleteCrewMemberTaskDto } from './dto/complete-crew-member-task.dto';
import { CrewMemberTaskFunction } from './helper/crew-member-task-function';
import { IncidentMessage } from 'src/task-incident/helper/incident-messages';
import { CrewMemberTaskMessage } from './helper/crew-member-task-message';
import {
  CrewMemberTask,
  CrewMemberTaskDocument,
} from './model/crew-member-task';
import {
  CrewMember,
  CrewMemberDocument,
} from 'src/crew-member-management/model/crew-member';
import {
  SubscriberFlightTask,
  SubscriberFlightTaskDocument,
} from 'src/subscriber-flight-task/model/subscriber-flight-task';
import { GpsCoordinates } from './interface/crew-member-task.interface';
import { IncidentStatus } from 'src/common/enum/incident-status';
import { CrewMemberHelper } from 'src/crew-member-auth/helper/crew-member-helper';
import { FileUploadService } from 'src/config/upload/upload.service';
import { CrewMemberLocationService } from './crew-member-location.service';
import { SubscriberTaskEmailFunction } from './helper/subscriber-task-email-function';
import { User, UserDocument } from 'src/user-auth/model/user';

@Injectable()
export class CrewMemberTaskService {
  constructor(
    @InjectModel(Incident.name)
    private readonly taskIncidentModel: Model<IncidentDocument>,
    @InjectModel(TaskImage.name)
    private readonly taskImageModel: Model<TaskImageDocument>,
    @InjectModel(CrewMemberTask.name)
    private readonly crewMemberTaskModel: Model<CrewMemberTaskDocument>,
    @InjectModel(CrewMember.name)
    private readonly crewMemberModel: Model<CrewMemberDocument>,
    @InjectModel(SubscriberFlightTask.name)
    private subscriberFlightTaskModel: Model<SubscriberFlightTaskDocument>,
    @InjectModel(User.name)
    private readonly userModel: Model<UserDocument>,
    private readonly crewMemberTaskFunction: CrewMemberTaskFunction,
    private readonly crewMemberHelper: CrewMemberHelper,
    private readonly fileUploadService: FileUploadService,
    private readonly locationService: CrewMemberLocationService,
    private readonly subscriberTaskEmailFunction: SubscriberTaskEmailFunction,
  ) {}

  async assignCrewMemberToTaskFromImages(
    imageIds: number | number[],
    dto: AssignCrewMemberTaskDto,
    assignedBy: number,
  ) {
    const idsArray = Array.isArray(imageIds) ? imageIds : [imageIds];

    const ongoingTask = await this.crewMemberTaskModel.findOne({
      crewMemberId: dto.assignee,
      status: {
        $in: [FlightTaskStatus.CREW_MEMBER_ACCEPTED, FlightTaskStatus.ON_GOING],
      },
    });

    if (ongoingTask) {
      throw new BadRequestException(
        CrewMemberTaskMessage.CREW_MEMBER_HAS_ONGOING_TASK,
      );
    }

    let taskId!: string;
    let gpsCoordinates!: GpsCoordinates;
    let location!: string;
    const imageAssigned: number[] = [];

    for (const imageId of idsArray) {
      const taskImage = await this.taskImageModel.findOne({ imageId }).lean();

      if (!taskImage) {
        throw new NotFoundException(IncidentMessage.TASK_IMAGE_NOT_FOUND);
      }
      taskImage.status = FlightTaskStatus.ASSIGNED_CREW_MEMBER;
      await this.taskImageModel.updateOne(
        { imageId },
        { status: taskImage.status },
      );

      const incidents = await this.taskIncidentModel.find({ imageId }).lean();

      if (!incidents.length) {
        throw new NotFoundException(IncidentMessage.INCIDENT_NOT_FOUND);
      }

      if (!taskId) {
        taskId = incidents[0].taskId;

        gpsCoordinates = incidents[0]
          .gpsCoordinates as unknown as GpsCoordinates;

        if (!gpsCoordinates) {
          throw new BadRequestException(
            CrewMemberTaskMessage.GPS_COORDINATES_MISSING,
          );
        }

        location = await this.crewMemberTaskFunction.getLocationFromCoordinates(
          gpsCoordinates.latitude,
          gpsCoordinates.longitude,
        );
      }

      imageAssigned.push(taskImage.imageId);
    }

    const { hour, minute } = this.crewMemberTaskFunction.parseTaskTime(
      dto.dueTime,
    );

    const dueDateTime = this.crewMemberTaskFunction.computeTaskDateTime(
      dto.dueDate,
      hour,
      minute,
    );

    await this.crewMemberTaskModel.create({
      taskId,
      crewMemberId: dto.assignee,
      imageAssigned,
      assignedBy,
      assignedAt: new Date(),
      dueDate: dto.dueDate,
      dueTime: dto.dueTime,
      dueDateTime,
      priority: dto.priority,
      note: dto.note,
      location,
      gpsCoordinates,
      status: FlightTaskStatus.ASSIGNED_CREW_MEMBER,
    });

    const subscriberTask =
      await this.subscriberFlightTaskModel.findOneAndUpdate(
        { taskId },
        { $set: { status: FlightTaskStatus.ASSIGNED_CREW_MEMBER } },
        { new: true },
      );

    if (!subscriberTask) {
      throw new NotFoundException(
        CrewMemberTaskMessage.SUBSCRIBER_TASK_NOT_FOUND,
      );
    }

    const result = await this.taskIncidentModel.updateMany(
      { taskId },
      { $set: { status: IncidentStatus.ASSIGNED_CREW_MEMBER } },
    );

    if (result.matchedCount === 0) {
      throw new NotFoundException(
        CrewMemberTaskMessage.INCIDENT_FOR_TASK_NOT_FOUND,
      );
    }

    try {
      const crewMember = await this.crewMemberModel
        .findOne({ crewMemberId: dto.assignee })
        .lean();

      if (crewMember) {
        await this.subscriberTaskEmailFunction.sendCrewMemberTaskAssignedEmail(
          crewMember.email,
          crewMember.firstName,
          taskId,
          location,
          dto.dueDate,
          dto.dueTime,
          dto.priority || 'Normal',
          dto.note,
        );
      }
    } catch (emailError) {
      console.error(
        'Error sending crew member task assigned email:',
        emailError,
      );
    }

    return {
      message: CrewMemberTaskMessage.ASSIGNMENT_SUCCESS,
    };
  }

  async retrieveCrewMembersBySubscriber(subscriberId: number) {
    const crewMembers = await this.crewMemberModel
      .find({ subscriber: subscriberId, status: 'active' })
      .select('crewMemberId firstName lastName')
      .lean();

    const formatted = crewMembers.map((cm) => ({
      crewMemberId: cm.crewMemberId,
      fullName: `${cm.firstName} ${cm.lastName}`,
    }));

    return {
      message: CrewMemberTaskMessage.CREW_MEMBERS_RETRIEVED_SUCCESS,
      data: formatted,
    };
  }

  async getCrewMemberTaskHistory(
    crewMemberId: number,
    query: GetCrewMemberTasksDto,
  ) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const filter: {
      crewMemberId: number;
      status?: string | { $in: string[] };
    } = { crewMemberId };

    if (query.status) {
      filter.status =
        query.status === FlightTaskStatus.ON_GOING
          ? { $in: [FlightTaskStatus.ON_GOING, FlightTaskStatus.REVIEW] }
          : query.status;
    }

    const sortOrder = query.sortBy?.startsWith('-') ? -1 : 1;
    const sortField = query.sortBy?.replace(/^-/, '') || 'assignedAt';
    const sort = [[sortField, sortOrder]] as [string, 1 | -1][];

    const [tasks, total, totalTasks, completedTasks, ongoingTask] =
      await Promise.all([
        this.crewMemberTaskModel
          .find(filter)
          .sort(sort)
          .skip(skip)
          .limit(limit)
          .lean(),

        this.crewMemberTaskModel.countDocuments(filter),

        this.crewMemberTaskModel.countDocuments({ crewMemberId }),

        this.crewMemberTaskModel.countDocuments({
          crewMemberId,
          status: {
            $in: [FlightTaskStatus.REVIEW, FlightTaskStatus.TASK_COMPLETED],
          },
        }),

        this.crewMemberTaskModel
          .findOne({
            crewMemberId,
            status: FlightTaskStatus.ON_GOING,
          })
          .lean(),
      ]);

    const totalPages = Math.ceil(total / limit);

    return {
      message: CrewMemberTaskMessage.TASK_HISTORY_RETRIEVED_SUCCESS,
      statistics: {
        totalTasks,
        completedTasks,
        pendingTasks: totalTasks - completedTasks,
      },
      ongoingTask: ongoingTask || null,
      data: tasks,
      pagination: {
        total,
        page,
        limit,
        totalPages,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1,
      },
    };
  }

  async getCrewMemberAllTasks(
    crewMemberId: number,
    query: GetCrewMemberTasksDto,
  ) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const filter: {
      crewMemberId: number;
      status?: string | { $in: string[] };
    } = { crewMemberId };

    if (query.status) {
      filter.status =
        query.status === FlightTaskStatus.ON_GOING
          ? { $in: [FlightTaskStatus.ON_GOING, FlightTaskStatus.REVIEW] }
          : query.status;
    }

    const sortOrder = query.sortBy?.startsWith('-') ? -1 : 1;
    const sortField = query.sortBy?.replace(/^-/, '') || 'assignedAt';
    const sort = [[sortField, sortOrder]] as [string, 1 | -1][];

    const [tasks, total] = await Promise.all([
      this.crewMemberTaskModel
        .find(filter)
        .sort(sort)
        .skip(skip)
        .limit(limit)
        .lean(),
      this.crewMemberTaskModel.countDocuments(filter),
    ]);

    const enrichedTasks = await Promise.all(
      tasks.map(async (task) => {
        const [flightTask, crewMember] = await Promise.all([
          this.subscriberFlightTaskModel
            .findOne({ taskId: task.taskId })
            .lean(),
          this.crewMemberModel
            .findOne({ crewMemberId: task.crewMemberId })
            .lean(),
        ]);

        return {
          ...task,
          flightTaskDetails: flightTask && {
            location: flightTask.location,
            area: flightTask.area,
            flightDate: flightTask.flightDate,
            flightTime: flightTask.flightTime,
          },
          crewMemberDetails: crewMember
            ? this.crewMemberHelper.formatCrewMemberResponse(crewMember)
            : null,
        };
      }),
    );

    const totalPages = Math.ceil(total / limit);

    return {
      message: CrewMemberTaskMessage.ALL_TASKS_RETRIEVED_SUCCESS,
      data: enrichedTasks,
      pagination: {
        total,
        page,
        limit,
        totalPages,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1,
      },
    };
  }

  async acceptCrewMemberTask(crewMemberId: number, crewMemberTaskId: string) {
    const task = await this.crewMemberTaskModel.findOne({
      taskId: crewMemberTaskId,
    });

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    if (task.status !== FlightTaskStatus.ASSIGNED_CREW_MEMBER) {
      throw new BadRequestException(
        CrewMemberTaskMessage.TASK_CANNOT_BE_ACCEPTED,
      );
    }

    task.status = FlightTaskStatus.CREW_MEMBER_ACCEPTED;
    task.acceptedAt = new Date();
    await task.save();

    try {
      const [subscriberTask, crewMember] = await Promise.all([
        this.subscriberFlightTaskModel.findOne({ taskId: task.taskId }).lean(),
        this.crewMemberModel
          .findOne({ crewMemberId: task.crewMemberId })
          .lean(),
      ]);

      if (subscriberTask?.createdBy && crewMember) {
        const subscriber = await this.userModel
          .findOne({ userId: subscriberTask.createdBy })
          .lean();

        if (subscriber) {
          await this.subscriberTaskEmailFunction.sendTaskAcceptedEmail(
            subscriber.email,
            subscriber.firstName,
            `${crewMember.firstName} ${crewMember.lastName}`,
            task.taskId,
            task.location,
            task.dueDate,
            task.dueTime,
          );
        }
      }
    } catch (emailError) {
      console.error('Error sending task accepted email:', emailError);
    }

    return {
      message: CrewMemberTaskMessage.TASK_ACCEPTED_SUCCESS,
      data: {
        taskId: task.taskId,
        status: task.status,
        acceptedAt: new Date(),
      },
    };
  }

  async getCrewMemberTaskDetails(
    crewMemberId: number,
    crewMemberTaskId: string,
  ) {
    const task = await this.crewMemberTaskModel
      .findOne({ taskId: crewMemberTaskId })
      .lean();

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    const [flightTask, crewMember, taskImages, incidents] = await Promise.all([
      this.subscriberFlightTaskModel.findOne({ taskId: task.taskId }).lean(),
      this.crewMemberModel.findOne({ crewMemberId: task.crewMemberId }).lean(),
      this.taskImageModel.find({ imageId: { $in: task.imageAssigned } }).lean(),
      this.taskIncidentModel
        .find({ imageId: { $in: task.imageAssigned } })
        .lean(),
    ]);

    return {
      message: CrewMemberTaskMessage.TASK_DETAILS_RETRIEVED_SUCCESS,
      data: {
        taskId: task.taskId,
        crewMemberId: task.crewMemberId,
        status: task.status,
        priority: task.priority,
        dueDate: task.dueDate,
        dueTime: task.dueTime,
        dueDateTime: task.dueDateTime,
        location: task.location,
        gpsCoordinates: task.gpsCoordinates,
        note: task.note,
        assignedAt: task.assignedAt,
        imageAssigned: task.imageAssigned,
        flightTaskDetails: flightTask && {
          taskId: flightTask.taskId,
          location: flightTask.location,
          area: flightTask.area,
          flightDate: flightTask.flightDate,
          flightTime: flightTask.flightTime,
          detectionPurpose: flightTask.detectionPurpose,
        },
        crewMemberDetails: crewMember
          ? this.crewMemberHelper.formatCrewMemberResponse(crewMember)
          : null,
        assignedImages: taskImages && {
          count: taskImages.length,
          images: taskImages.map((img) => ({
            imageId: img.imageId,
            filename: img.filename,
            imageUrl: img.imageUrl,
            captureTimestamp: img.captureTimestamp,
            totalIncidents: img.totalIncidents,
            totalWasteAreaSqm: img.totalWasteAreaSqm,
          })),
        },
        incidents: incidents && {
          count: incidents.length,
          details: incidents.map((incident) => ({
            incidentId: incident.incidentId,
            imageId: incident.imageId,
            wasteType: incident.wasteType,
            severityLevel: incident.severityLevel,
            confidenceScore: incident.confidenceScore,
            areaSquareMeters: incident.areaSquareMeters,
            gpsCoordinates: incident.gpsCoordinates,
            status: incident.status,
          })),
        },
      },
    };
  }

  async beginCrewMemberTask(crewMemberId: number, crewMemberTaskId: string) {
    const task = await this.crewMemberTaskModel.findOne({
      taskId: crewMemberTaskId,
    });

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    if (task.status !== FlightTaskStatus.CREW_MEMBER_ACCEPTED) {
      throw new BadRequestException(CrewMemberTaskMessage.TASK_CANNOT_BE_BEGUN);
    }

    task.status = FlightTaskStatus.ON_GOING;
    task.begunAt = new Date();
    await task.save();

    return {
      message: CrewMemberTaskMessage.TASK_BEGUN_SUCCESS,
      data: {
        taskId: task.taskId,
        status: task.status,
        begunAt: new Date(),
      },
    };
  }

  async rejectCrewMemberTask(
    crewMemberId: number,
    crewMemberTaskId: string,
    dto: RejectCrewMemberTaskDto,
  ) {
    const task = await this.crewMemberTaskModel.findOne({
      taskId: crewMemberTaskId,
    });

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    if (task.status !== FlightTaskStatus.ASSIGNED_CREW_MEMBER) {
      throw new BadRequestException(
        CrewMemberTaskMessage.TASK_CANNOT_BE_REJECTED,
      );
    }

    task.status = FlightTaskStatus.REJECTED;
    task.rejectionReason = dto.reason;
    task.rejectedAt = new Date();
    await task.save();

    try {
      const [subscriberTask, crewMember] = await Promise.all([
        this.subscriberFlightTaskModel.findOne({ taskId: task.taskId }).lean(),
        this.crewMemberModel
          .findOne({ crewMemberId: task.crewMemberId })
          .lean(),
      ]);

      if (subscriberTask?.createdBy && crewMember) {
        const subscriber = await this.userModel
          .findOne({ userId: subscriberTask.createdBy })
          .lean();

        if (subscriber) {
          await this.subscriberTaskEmailFunction.sendTaskRejectedEmail(
            subscriber.email,
            subscriber.firstName,
            `${crewMember.firstName} ${crewMember.lastName}`,
            task.taskId,
            task.location,
            task.dueDate,
            task.rejectionReason || '',
          );
        }
      }
    } catch (emailError) {
      console.error('Error sending task rejected email:', emailError);
    }

    return {
      message: CrewMemberTaskMessage.TASK_REJECTED_SUCCESS,
      data: {
        taskId: task.taskId,
        status: task.status,
        rejectionReason: task.rejectionReason,
        rejectedAt: new Date(),
      },
    };
  }

  async stopCrewMemberTask(
    crewMemberId: number,
    crewMemberTaskId: string,
    dto: StopCrewMemberTaskDto,
  ) {
    const task = await this.crewMemberTaskModel.findOne({
      taskId: crewMemberTaskId,
    });

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    if (task.status !== FlightTaskStatus.ON_GOING) {
      throw new BadRequestException(
        CrewMemberTaskMessage.TASK_CANNOT_BE_STOPPED,
      );
    }

    task.status = FlightTaskStatus.STOPPED;
    task.stoppedReason = dto.reason;
    task.stoppedAt = new Date();
    await task.save();

    await this.locationService.deleteLocationForTask(
      crewMemberId,
      crewMemberTaskId,
    );

    try {
      const [subscriberTask, crewMember] = await Promise.all([
        this.subscriberFlightTaskModel.findOne({ taskId: task.taskId }).lean(),
        this.crewMemberModel
          .findOne({ crewMemberId: task.crewMemberId })
          .lean(),
      ]);

      if (subscriberTask?.createdBy && crewMember) {
        const subscriber = await this.userModel
          .findOne({ userId: subscriberTask.createdBy })
          .lean();

        if (subscriber) {
          await this.subscriberTaskEmailFunction.sendTaskStoppedEmail(
            subscriber.email,
            subscriber.firstName,
            `${crewMember.firstName} ${crewMember.lastName}`,
            task.taskId,
            task.location,
            task.dueDate,
            task.stoppedReason || '',
          );
        }
      }
    } catch (emailError) {
      console.error('Error sending task stopped email:', emailError);
    }

    return {
      message: CrewMemberTaskMessage.TASK_STOPPED_SUCCESS,
      data: {
        taskId: task.taskId,
        status: task.status,
        stoppedReason: task.stoppedReason,
        stoppedAt: new Date(),
      },
    };
  }

  async completeCrewMemberTask(
    crewMemberId: number,
    crewMemberTaskId: string,
    dto: CompleteCrewMemberTaskDto,
    files?: Express.Multer.File[],
  ) {
    const task = await this.crewMemberTaskModel.findOne({
      taskId: crewMemberTaskId,
    });

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    if (task.crewMemberId !== crewMemberId) {
      throw new BadRequestException(
        CrewMemberTaskMessage.UNAUTHORIZED_TASK_ACCESS,
      );
    }

    if (task.status !== FlightTaskStatus.ON_GOING) {
      throw new BadRequestException(
        CrewMemberTaskMessage.TASK_CANNOT_BE_COMPLETED,
      );
    }

    if (!files || files.length === 0) {
      throw new BadRequestException(
        CrewMemberTaskMessage.COMPLETION_EVIDENCE_REQUIRED,
      );
    }

    if (files.length > 5) {
      throw new BadRequestException('Maximum 5 files allowed');
    }

    const completionEvidence: string[] = [];
    for (const file of files) {
      const uploadedUrl = await this.fileUploadService.handleFileUpload(file);
      completionEvidence.push(uploadedUrl);
    }

    task.status = FlightTaskStatus.REVIEW;
    task.completionEvidence = completionEvidence;
    task.completedAt = new Date();
    await task.save();

    await this.locationService.deleteLocationForTask(
      crewMemberId,
      crewMemberTaskId,
    );

    try {
      const [subscriberTask, crewMember] = await Promise.all([
        this.subscriberFlightTaskModel.findOne({ taskId: task.taskId }).lean(),
        this.crewMemberModel
          .findOne({ crewMemberId: task.crewMemberId })
          .lean(),
      ]);

      if (subscriberTask?.createdBy && crewMember) {
        const subscriber = await this.userModel
          .findOne({ userId: subscriberTask.createdBy })
          .lean();

        if (subscriber) {
          await this.subscriberTaskEmailFunction.sendTaskCompletedEmail(
            subscriber.email,
            subscriber.firstName,
            `${crewMember.firstName} ${crewMember.lastName}`,
            task.taskId,
            task.location,
            task.dueDate,
            task.completionEvidence.length,
          );
        }
      }
    } catch (emailError) {
      console.error('Error sending task completed email:', emailError);
    }

    return {
      message: CrewMemberTaskMessage.TASK_COMPLETED_SUCCESS,
      data: {
        taskId: task.taskId,
        status: task.status,
        completionEvidenceCount: task.completionEvidence.length,
        completedAt: new Date(),
      },
    };
  }

  async getSubscriberCrewMemberTaskLogs(
    subscriberId: number,
    query: GetCrewMemberTasksDto,
  ) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    const skip = (page - 1) * limit;

    const filter: { assignedBy: number; status?: string } = {
      assignedBy: subscriberId,
    };

    if (query.status) {
      filter.status = query.status;
    }

    const sortOrder = query.sortBy?.startsWith('-') ? -1 : 1;
    const sortField = query.sortBy?.replace(/^-/, '') || 'assignedAt';
    const sort = [[sortField, sortOrder]] as [string, 1 | -1][];

    const [tasks, total] = await Promise.all([
      this.crewMemberTaskModel
        .find(filter)
        .sort(sort)
        .skip(skip)
        .limit(limit)
        .lean(),
      this.crewMemberTaskModel.countDocuments(filter),
    ]);

    const enrichedTasks = await Promise.all(
      tasks.map(async (task) => {
        const crewMember = await this.crewMemberModel
          .findOne({ crewMemberId: task.crewMemberId })
          .select('firstName lastName')
          .lean();

        const timeOnSite = this.crewMemberTaskFunction.calculateTimeOnSite(
          task.begunAt,
          task.completedAt,
          task.stoppedAt,
        );

        return {
          taskId: task.taskId,
          status: task.status,
          size: task.imageAssigned?.length || 0,
          location: task.location,
          timeOnSite: timeOnSite || null,
          crewMemberName: crewMember
            ? `${crewMember.firstName} ${crewMember.lastName}`
            : 'Unknown',
          dueDate: this.crewMemberTaskFunction.formatDate(task.dueDateTime),
        };
      }),
    );

    const totalPages = Math.ceil(total / limit);

    return {
      message: 'Crew member task logs retrieved successfully',
      data: enrichedTasks,
      pagination: {
        total,
        page,
        limit,
        totalPages,
        hasNextPage: page < totalPages,
        hasPrevPage: page > 1,
      },
    };
  }

  async getSubscriberCrewMemberTaskLogDetails(
    subscriberId: number,
    taskId: string,
  ) {
    const task = await this.crewMemberTaskModel
      .findOne({ taskId, assignedBy: subscriberId })
      .lean();

    if (!task) {
      throw new NotFoundException(CrewMemberTaskMessage.TASK_NOT_FOUND);
    }

    const [crewMember] = await Promise.all([
      this.crewMemberModel
        .findOne({ crewMemberId: task.crewMemberId })
        .select('firstName lastName')
        .lean(),
      this.taskImageModel
        .find({ imageId: { $in: task.imageAssigned } })
        .select('imageId imageUrl')
        .lean(),
    ]);

    const timeOnSite = this.crewMemberTaskFunction.calculateTimeOnSite(
      task.begunAt,
      task.completedAt,
      task.stoppedAt,
    );

    const completedTimeFormatted = task.completedAt
      ? this.crewMemberTaskFunction.formatRelativeTime(task.completedAt)
      : task.stoppedAt
        ? this.crewMemberTaskFunction.formatRelativeTime(task.stoppedAt)
        : null;

    type TimelineEvent = {
      event: string;
      timestamp: string;
      formattedDateTime: string;
      reason?: string;
    };

    const timeline: TimelineEvent[] = [];
    if (task.assignedAt) {
      timeline.push({
        event: 'Task Assigned',
        timestamp: this.crewMemberTaskFunction.formatDateTime(task.assignedAt),
        formattedDateTime: this.crewMemberTaskFunction.formatDateTime(
          task.assignedAt,
        ),
      });
    }

    if (task.acceptedAt) {
      timeline.push({
        event: 'Task Accepted',
        timestamp: this.crewMemberTaskFunction.formatDateTime(task.assignedAt),
        formattedDateTime: this.crewMemberTaskFunction.formatDateTime(
          task.acceptedAt,
        ),
      });
    }

    if (task.status === FlightTaskStatus.REJECTED && task.rejectionReason) {
      const rejectedAt = task.assignedAt;
      timeline.push({
        event: 'Task Rejected',
        timestamp: this.crewMemberTaskFunction.formatDateTime(rejectedAt),
        formattedDateTime:
          this.crewMemberTaskFunction.formatDateTime(rejectedAt),
        reason: task.rejectionReason,
      });
    }

    if (task.begunAt) {
      timeline.push({
        event: 'Task Begun',
        timestamp: this.crewMemberTaskFunction.formatDateTime(task.begunAt),
        formattedDateTime: this.crewMemberTaskFunction.formatDateTime(
          task.begunAt,
        ),
      });
    }

    if (task.completedAt) {
      timeline.push({
        event: 'Task Completed',
        timestamp: this.crewMemberTaskFunction.formatDateTime(task.completedAt),
        formattedDateTime: this.crewMemberTaskFunction.formatDateTime(
          task.completedAt,
        ),
      });
    } else if (task.stoppedAt) {
      timeline.push({
        event: 'Task Stopped',
        timestamp: this.crewMemberTaskFunction.formatDateTime(task.stoppedAt),
        formattedDateTime: this.crewMemberTaskFunction.formatDateTime(
          task.stoppedAt,
        ),
        reason: task.stoppedReason,
      });
    }

    timeline.sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    );

    return {
      message: 'Crew member task log details retrieved successfully',
      data: {
        taskId: task.taskId,
        status: task.status,
        size: task.imageAssigned?.length || 0,
        location: task.location,
        gpsCoordinates: task.gpsCoordinates || null,
        timeOnSite: timeOnSite || null,
        crewMemberName: crewMember
          ? `${crewMember.firstName} ${crewMember.lastName}`
          : 'Unknown',
        dueDate: this.crewMemberTaskFunction.formatDate(task.dueDateTime),
        completedTimeFormatted: completedTimeFormatted,
        evidence:
          task.status === FlightTaskStatus.REVIEW ||
          task.status === FlightTaskStatus.TASK_COMPLETED ||
          task.status === FlightTaskStatus.COMPLETED
            ? task.completionEvidence || []
            : null,
        timeline: timeline,
      },
    };
  }
}

'''
