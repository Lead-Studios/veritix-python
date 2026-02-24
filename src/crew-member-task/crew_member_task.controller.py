"""Auto-converted from TypeScript.
Original file: crew-member-task/crew-member-task.controller.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  Body,
  Controller,
  Get,
  Post,
  UseGuards,
  Query,
  Param,
  UseInterceptors,
  UploadedFiles,
  HttpStatus,
  HttpException,
} from '@nestjs/common';
import { CrewMemberTaskService } from './crew-member-task.service';
import { CrewJwtAuthGuard } from 'src/crew-member-auth/guard/jwt.ath.guard';
import { CurrentCrewMember } from 'src/crew-member-auth/decorators/current-crew-member.decorator';
import { JwtAuthGuard } from 'src/user-auth/guard/jwt.auth.guard';
import { Roles } from 'src/user-auth/decorators/roles.decorators';
import { RolesGuard } from 'src/user-auth/guard/roles.guard';
import { CurrentUser } from 'src/user-auth/decorators/current.user.decorators';
import { User } from 'src/user-auth/model/user';
import { UserRole } from 'src/common/enum/user-role';
import {
  ApiBody,
  ApiOkResponse,
  ApiTags,
  ApiQuery,
  ApiConsumes,
  ApiBearerAuth,
  ApiOperation,
} from '@nestjs/swagger';
import { FilesInterceptor } from '@nestjs/platform-express';
import { AssignCrewMemberTaskDto } from './dto/assign-crew-member-task.dto';
import { GetCrewMemberTasksDto } from './dto/get-crew-member-tasks.dto';
import { RejectCrewMemberTaskDto } from './dto/reject-crew-member-task.dto';
import { StopCrewMemberTaskDto } from './dto/stop-crew-member-task.dto';
import { TaskPriority } from 'src/common/enum/task-priority';
import { CrewMember } from 'src/crew-member-management/model/crew-member';
import { CrewMemberLocationService } from './crew-member-location.service';

@ApiTags('Crew Member Task Management')
@Controller('api/v1/crew-member-task')
export class CrewMemberTaskController {
  constructor(
    private readonly crewMemberTaskService: CrewMemberTaskService,
    private readonly locationService: CrewMemberLocationService,
  ) {}

  @Post('assign')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({ summary: 'Assign Crew Member to Task from Task Images' })
  @ApiBody({
    description:
      'Payload for assigning a crew member to one or more task images',
    schema: {
      example: {
        taskImageIds: [1, 2, 3],
        assignee: 101,
        note: 'Inspect these areas carefully',
        dueDate: {
          type: 'string',
          format: 'date',
          description: 'Start date of the flight task (YYYY-MM-DD)',
        },
        dueTime: {
          type: 'string',
          description: 'Time in HH:mm AM/PM format',
        },
        priority: TaskPriority.LOW,
      },
    },
  })
  @ApiOkResponse({
    description: 'Crew member assigned successfully',
    schema: {
      example: {
        message: 'Crew member assigned successfully',
      },
    },
  })
  async assignCrewMember(
    @Body() body: { taskImageIds: number | number[] } & AssignCrewMemberTaskDto,
    @CurrentUser() user: User,
  ) {
    const { taskImageIds, ...dto } = body;
    return await this.crewMemberTaskService.assignCrewMemberToTaskFromImages(
      taskImageIds,
      dto,
      user.userId,
    );
  }

  @Get('assignees/all')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({ summary: 'Retrieve All Crew Members for Subscriber' })
  @ApiOkResponse({
    description: 'All crew members for the subscriber',
    schema: {
      example: {
        message: 'Crew members retrieved successfully',
        data: [
          {
            crewMemberId: 1,
            firstName: 'Moshood',
            lastName: 'Jaji',
            email: 'moshoodjaji.a@gmail.com',
            phoneNumber: '+2348090686548',
          },
        ],
      },
    },
  })
  async retrieveCrewMembersBySubscriber(@CurrentUser() user: User) {
    return this.crewMemberTaskService.retrieveCrewMembersBySubscriber(
      user.userId,
    );
  }

  @Get('history')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Get Crew Member Task History' })
  @ApiOkResponse({
    description: 'Crew member task history retrieved successfully',
    schema: {
      example: {
        message: 'Task history retrieved successfully',
        statistics: {
          totalTasks: 25,
          completedTasks: 18,
          pendingTasks: 7,
        },
        ongoingTask: {
          _id: '507f1f77bcf86cd799439012',
          taskId: 'TASK-2024-002',
          crewMemberId: 101,
          imageAssigned: [4, 5, 6],
          assignedBy: 5,
          assignedAt: '2024-12-22T14:00:00Z',
          dueDate: '2024-12-28',
          dueTime: '04:00 PM',
          dueDateTime: '2024-12-28T16:00:00Z',
          priority: 'High',
          note: 'Urgent inspection required',
          status: 'Ongoing',
          location: 'Ikoyi, Lagos',
          gpsCoordinates: { latitude: 6.4587, longitude: 3.6205 },
        },
        data: [
          {
            _id: '507f1f77bcf86cd799439011',
            taskId: 'TASK-2024-001',
            crewMemberId: 101,
            imageAssigned: [1, 2, 3],
            assignedBy: 5,
            assignedAt: '2024-12-20T10:30:00Z',
            dueDate: '2024-12-25',
            dueTime: '02:00 PM',
            dueDateTime: '2024-12-25T14:00:00Z',
            priority: 'Normal',
            note: 'Inspect these areas carefully',
            status: 'Completed',
            location: 'Lagos, Nigeria',
            gpsCoordinates: { latitude: 6.5244, longitude: 3.3792 },
          },
        ],
        pagination: {
          total: 10,
          page: 1,
          limit: 10,
          totalPages: 1,
          hasNextPage: false,
          hasPrevPage: false,
        },
      },
    },
  })
  @ApiQuery({
    name: 'status',
    required: false,
    description:
      'Filter by task status (New, Accepted, Ongoing, Completed, etc.)',
  })
  @ApiQuery({
    name: 'page',
    required: false,
    type: Number,
    description: 'Page number for pagination (default: 1)',
  })
  @ApiQuery({
    name: 'limit',
    required: false,
    type: Number,
    description: 'Number of records per page (default: 10)',
  })
  @ApiQuery({
    name: 'sortBy',
    required: false,
    description: 'Sort field (prefix with - for descending, e.g., -assignedAt)',
  })
  async getTaskHistory(
    @CurrentCrewMember() user: CrewMember,
    @Query() query: GetCrewMemberTasksDto,
  ) {
    return this.crewMemberTaskService.getCrewMemberTaskHistory(
      user.crewMemberId,
      query,
    );
  }

  @Get('all')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Get All Crew Member Tasks with Filtering' })
  @ApiOkResponse({
    description: 'All crew member tasks retrieved successfully with filtering',
    schema: {
      example: {
        message: 'All tasks retrieved successfully',
        data: [
          {
            _id: '507f1f77bcf86cd799439011',
            taskId: 'TASK-2024-001',
            crewMemberId: 101,
            imageAssigned: [1, 2, 3],
            assignedBy: 5,
            assignedAt: '2024-12-20T10:30:00Z',
            dueDate: '2024-12-25',
            dueTime: '02:00 PM',
            dueDateTime: '2024-12-25T14:00:00Z',
            priority: 'Normal',
            note: 'Inspect these areas carefully',
            status: 'Ongoing',
            location: 'Lagos, Nigeria',
            gpsCoordinates: { latitude: 6.5244, longitude: 3.3792 },
            flightTaskDetails: {
              location: 'Lekki Conservation Centre, Lagos',
              area: 'Conservation Area 1',
              flightDate: '2024-12-20',
              flightTime: '10:00 AM',
            },
            crewMemberDetails: {
              firstName: 'Moshood',
              lastName: 'Jaji',
              email: 'moshoodjaji.a@gmail.com',
              phoneNumber: '+2348090686548',
            },
          },
        ],
        pagination: {
          total: 10,
          page: 1,
          limit: 10,
          totalPages: 1,
          hasNextPage: false,
          hasPrevPage: false,
        },
      },
    },
  })
  @ApiQuery({
    name: 'status',
    required: false,
    description: 'Filter by task status (e.g., Ongoing, Completed, Accepted)',
  })
  @ApiQuery({
    name: 'page',
    required: false,
    type: Number,
    description: 'Page number for pagination (default: 1)',
  })
  @ApiQuery({
    name: 'limit',
    required: false,
    type: Number,
    description: 'Number of records per page (default: 10)',
  })
  @ApiQuery({
    name: 'sortBy',
    required: false,
    description:
      'Sort field (prefix with - for descending, e.g., -dueDateTime)',
  })
  async getAllTasks(
    @CurrentCrewMember() user: CrewMember,
    @Query() query: GetCrewMemberTasksDto,
  ) {
    return this.crewMemberTaskService.getCrewMemberAllTasks(
      user.crewMemberId,
      query,
    );
  }

  @Post(':taskId/accept')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Accept a Crew Member Task' })
  @ApiOkResponse({
    description: 'Task accepted successfully',
    schema: {
      example: {
        message: 'Task accepted successfully',
        data: {
          taskId: 'TASK-2025-001',
          status: 'Accepted',
          acceptedAt: '2025-12-27T10:30:00Z',
        },
      },
    },
  })
  async acceptTask(
    @Param('taskId') taskId: string,
    @CurrentCrewMember() user: CrewMember,
  ) {
    return this.crewMemberTaskService.acceptCrewMemberTask(
      user.crewMemberId,
      taskId,
    );
  }

  @Get(':taskId/details')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Get Crew Member Task Details' })
  @ApiOkResponse({
    description: 'Task details retrieved successfully',
    schema: {
      example: {
        message: 'Task details retrieved successfully',
        data: {
          taskId: 'TASK-2025-001',
          crewMemberId: 101,
          status: 'Crew Member Assigned',
          priority: 'High',
          dueDate: '2025-12-25',
          dueTime: '02:00 PM',
          dueDateTime: '2025-12-25T14:00:00Z',
          location: 'Lagos, Nigeria',
          gpsCoordinates: { latitude: 6.5244, longitude: 3.3792 },
          note: 'Inspect these areas carefully',
          assignedAt: '2024-12-20T10:30:00Z',
          imageAssigned: [1, 2, 3],
          flightTaskDetails: {
            taskId: 'TASK-2025-001',
            location: 'Lekki Conservation Centre',
            area: 'Conservation Area 1',
            flightDate: '2025-12-20',
            flightTime: '10:00 AM',
            detectionPurpose: 'New Detection',
          },
          crewMemberDetails: {
            crewMemberId: 101,
            firstName: 'Moshood',
            lastName: 'Jaji',
            email: 'moshood@example.com',
            phoneNumber: '+2348090686548',
          },
          assignedImages: {
            count: 3,
            images: [
              {
                imageId: 1,
                filename: 'image_001.jpg',
                imageUrl:
                  'https://lisavue-media-storage.s3.amazonaws.com/image_001.jpg',
                captureTimestamp: '2025-12-20T10:15:00Z',
                totalIncidents: 2,
                totalWasteAreaSqm: 145.5,
              },
            ],
          },
          incidents: {
            count: 5,
            details: [
              {
                incidentId: 'INC-001',
                imageId: 1,
                wasteType: 'Plastic',
                severityLevel: 'High',
                confidenceScore: 0.95,
                areaSquareMeters: 50.25,
                gpsCoordinates: { latitude: 6.5244, longitude: 3.3792 },
                status: 'Pending',
              },
            ],
          },
        },
      },
    },
  })
  async getTaskDetails(
    @Param('taskId') taskId: string,
    @CurrentCrewMember() user: CrewMember,
  ) {
    const taskDetails =
      await this.crewMemberTaskService.getCrewMemberTaskDetails(
        user.crewMemberId,
        taskId,
      );

    const navigation = await this.locationService.getTaskNavigation(
      user.crewMemberId,
      taskId,
    );

    return {
      ...taskDetails,
      navigation: navigation || null,
    };
  }

  @Post(':taskId/enable-location')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({
    summary: 'Enable Location Tracking for a Task',
    description:
      "Enables GPS location tracking for a crew member on an accepted task. Fetches the crew member's current location from the database. Must be called before beginning the task. Crew member must have shared their location via WebSocket first.",
  })
  @ApiOkResponse({
    description: 'Location tracking enabled successfully with navigation data',
    schema: {
      example: {
        message: 'Location tracking enabled successfully',
        data: {
          crewMemberId: 101,
          taskId: 'TASK-2025-001',
          currentLocation: {
            latitude: 40.7128,
            longitude: -74.006,
            accuracy: 10,
            altitude: 5,
            speed: 0,
            heading: 0,
            timestamp: '2025-12-27T11:30:00Z',
          },
          taskDestination: {
            latitude: 40.758,
            longitude: -73.9855,
            taskId: 'TASK-2025-001',
            location: 'Times Square',
          },
          isActive: true,
          distance: 5650,
        },
        success: true,
      },
    },
  })
  async enableLocationTracking(
    @Param('taskId') taskId: string,
    @CurrentCrewMember() user: CrewMember,
  ) {
    const hasLocation = await this.locationService.hasLocationForTask(
      user.crewMemberId,
      taskId,
    );

    if (!hasLocation) {
      throw new HttpException(
        {
          message:
            'Location not detected. Please ensure location services are enabled on your device and try again.',
          success: false,
          error: 'LOCATION_NOT_SHARED',
        },
        HttpStatus.BAD_REQUEST,
      );
    }

    const navigationData = await this.locationService.getTaskNavigation(
      user.crewMemberId,
      taskId,
    );

    if (!navigationData) {
      throw new HttpException(
        {
          message: 'Task not found or crew member does not own this task',
          success: false,
          error: 'TASK_NOT_FOUND',
        },
        HttpStatus.NOT_FOUND,
      );
    }

    return {
      message: 'Location tracking enabled successfully',
      data: navigationData,
      success: true,
    };
  }

  @Post(':taskId/begin')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({
    summary: 'Begin a Crew Member Task',
    description:
      'Starts working on an accepted task. Location tracking must be enabled before calling this endpoint.',
  })
  @ApiOkResponse({
    description: 'Task begun successfully',
    schema: {
      example: {
        message: 'Task begun successfully',
        data: {
          taskId: 'TASK-2025-001',
          status: 'Ongoing',
          begunAt: '2025-12-27T11:00:00Z',
        },
      },
    },
  })
  async beginTask(
    @Param('taskId') taskId: string,
    @CurrentCrewMember() user: CrewMember,
  ) {
    return this.crewMemberTaskService.beginCrewMemberTask(
      user.crewMemberId,
      taskId,
    );
  }

  @Post(':taskId/reject')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Reject a Crew Member Task' })
  @ApiBody({
    description: 'Payload for rejecting a task with reason',
    type: RejectCrewMemberTaskDto,
    examples: {
      example1: {
        value: {
          reason:
            'I am unable to complete this task due to equipment malfunction',
        },
      },
    },
  })
  @ApiOkResponse({
    description: 'Task rejected successfully',
    schema: {
      example: {
        message: 'Task rejected successfully',
        data: {
          taskId: 'TASK-2025-001',
          status: 'Declined',
          rejectionReason:
            'I am unable to complete this task due to equipment malfunction',
          rejectedAt: '2025-12-27T11:30:00Z',
        },
      },
    },
  })
  async rejectTask(
    @Param('taskId') taskId: string,
    @Body() dto: RejectCrewMemberTaskDto,
    @CurrentCrewMember() user: CrewMember,
  ) {
    return this.crewMemberTaskService.rejectCrewMemberTask(
      user.crewMemberId,
      taskId,
      dto,
    );
  }

  @Post(':taskId/stop')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Stop a Crew Member Task' })
  @ApiBody({
    description: 'Payload for stopping an ongoing task with reason',
    type: StopCrewMemberTaskDto,
    examples: {
      example1: {
        value: {
          reason:
            'I encountered technical difficulties and need to pause the work',
        },
      },
    },
  })
  @ApiOkResponse({
    description: 'Task stopped successfully',
    schema: {
      example: {
        message: 'Task stopped successfully',
        data: {
          taskId: 'TASK-2025-001',
          status: 'Accepted',
          stoppedReason:
            'I encountered technical difficulties and need to pause the work',
          stoppedAt: '2025-12-27T12:00:00Z',
        },
      },
    },
  })
  async stopTask(
    @Param('taskId') taskId: string,
    @Body() dto: StopCrewMemberTaskDto,
    @CurrentCrewMember() user: CrewMember,
  ) {
    return this.crewMemberTaskService.stopCrewMemberTask(
      user.crewMemberId,
      taskId,
      dto,
    );
  }

  @Post(':taskId/complete')
  @UseGuards(CrewJwtAuthGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({ summary: 'Complete a Crew Member Task with Evidence' })
  @UseInterceptors(FilesInterceptor('evidenceFiles', 5))
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    description: 'Complete task with evidence files (max 5 files)',
    schema: {
      type: 'object',
      properties: {
        evidenceFiles: {
          type: 'array',
          items: {
            type: 'string',
            format: 'binary',
          },
          description:
            'Evidence files (max 5, supported: JPG, PNG, PDF, Word, Excel)',
        },
      },
      required: ['evidenceFiles'],
    },
  })
  @ApiOkResponse({
    description: 'Task completed successfully',
    schema: {
      example: {
        message: 'Task completed successfully',
        data: {
          taskId: 'TASK-2024-001',
          status: 'Completed',
          completionEvidenceCount: 3,
          completedAt: '2024-12-27T12:30:00Z',
        },
      },
    },
  })
  async completeTask(
    @Param('taskId') taskId: string,
    @UploadedFiles() files: Express.Multer.File[],
    @CurrentCrewMember() user: CrewMember,
  ) {
    return this.crewMemberTaskService.completeCrewMemberTask(
      user.crewMemberId,
      taskId,
      { evidenceFiles: files },
      files,
    );
  }

  @Get('subscriber/crew-member-task-logs')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({
    summary: 'Get All Crew Member Task Logs for Subscriber',
    description:
      'Retrieves all crew member task logs assigned by the authenticated subscriber with pagination support.',
  })
  @ApiOkResponse({
    description: 'Crew member task logs retrieved successfully',
    schema: {
      example: {
        message: 'Crew member task logs retrieved successfully',
        data: [
          {
            taskId: 'TASK-2024-001',
            status: 'Task Completed',
            size: 3,
            location: 'Lagos, Nigeria',
            timeOnSite: '2 hours 30 minutes',
            crewMemberName: 'John Doe',
            dueDate: '25th December 2024',
          },
        ],
        pagination: {
          total: 10,
          page: 1,
          limit: 10,
          totalPages: 1,
          hasNextPage: false,
          hasPrevPage: false,
        },
      },
    },
  })
  @ApiQuery({
    name: 'status',
    required: false,
    description: 'Filter by task status',
  })
  @ApiQuery({
    name: 'page',
    required: false,
    type: Number,
    description: 'Page number for pagination (default: 1)',
  })
  @ApiQuery({
    name: 'limit',
    required: false,
    type: Number,
    description: 'Number of records per page (default: 10)',
  })
  @ApiQuery({
    name: 'sortBy',
    required: false,
    description: 'Sort field (prefix with - for descending, e.g., -assignedAt)',
  })
  async getSubscriberCrewMemberTaskLogs(
    @CurrentUser() user: User,
    @Query() query: GetCrewMemberTasksDto,
  ) {
    return this.crewMemberTaskService.getSubscriberCrewMemberTaskLogs(
      user.userId,
      query,
    );
  }

  @Get('subscriber/crew-member-task-log/:taskId')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiBearerAuth('JWT-auth')
  @ApiOperation({
    summary: 'Get Crew Member Task Log Details',
    description:
      'Retrieves detailed information about a specific crew member task log including GPS coordinates, evidence, and timeline.',
  })
  @ApiOkResponse({
    description: 'Crew member task log details retrieved successfully',
    schema: {
      example: {
        message: 'Crew member task log details retrieved successfully',
        data: {
          taskId: 'TASK-2024-001',
          status: 'Task Completed',
          size: 3,
          location: 'Lagos, Nigeria',
          gpsCoordinates: {
            latitude: 6.5244,
            longitude: 3.3792,
          },
          timeOnSite: '2 hours 30 minutes',
          crewMemberName: 'John Doe',
          dueDate: '25th December 2024',
          completedTimeFormatted: '10 minutes ago',
          evidence: [
            'https://bucket.s3.amazonaws.com/evidence1.jpg',
            'https://bucket.s3.amazonaws.com/evidence2.jpg',
          ],
          timeline: [
            {
              event: 'Task Assigned',
              timestamp: '2024-12-20T10:30:00Z',
              formattedDateTime: '20th December 2024 at 10:30 AM',
            },
            {
              event: 'Task Accepted',
              timestamp: '2024-12-20T11:00:00Z',
              formattedDateTime: '20th December 2024 at 11:00 AM',
            },
            {
              event: 'Task Begun',
              timestamp: '2024-12-20T12:00:00Z',
              formattedDateTime: '20th December 2024 at 12:00 PM',
            },
            {
              event: 'Task Completed',
              timestamp: '2024-12-20T14:30:00Z',
              formattedDateTime: '20th December 2024 at 2:30 PM',
            },
          ],
        },
      },
    },
  })
  async getSubscriberCrewMemberTaskLogDetails(
    @Param('taskId') taskId: string,
    @CurrentUser() user: User,
  ) {
    return this.crewMemberTaskService.getSubscriberCrewMemberTaskLogDetails(
      user.userId,
      taskId,
    );
  }
}

'''
