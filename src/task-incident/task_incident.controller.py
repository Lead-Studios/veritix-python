"""Auto-converted from TypeScript.
Original file: task-incident/task-incident.controller.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  Controller,
  Post,
  Body,
  HttpCode,
  HttpStatus,
  UseGuards,
  DefaultValuePipe,
  Get,
  Param,
  ParseIntPipe,
  Query,
  Req,
} from '@nestjs/common';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiBody,
  ApiParam,
  ApiQuery,
  ApiOkResponse,
} from '@nestjs/swagger';
import { TaskIncidentService } from './task-incident.service';
import { CreateTaskIncidentDto } from './dto/create-task-incident.dto';
import { Incident } from './model/incident';
import { TaskImage } from './model/task-image';
import { ApiKeyGuard } from 'src/config/api-guard/api-key-guard';
import { UserRole } from 'src/common/enum/user-role';
import { Roles } from 'src/user-auth/decorators/roles.decorators';
import { JwtAuthGuard } from 'src/user-auth/guard/jwt.auth.guard';
import { RolesGuard } from 'src/user-auth/guard/roles.guard';
import { CurrentUser } from 'src/user-auth/decorators/current.user.decorators';
import { User } from 'src/user-auth/model/user';
import { RetrieveSubscriberIncidentsQuery } from './dto/retrieve-subscriber-incidents.query';
import { FlightTaskStatus } from 'src/common/enum/flight-task-status';

@ApiTags('Task Incidents')
@Controller('api/v1/task-incidents')
export class TaskIncidentController {
  constructor(private readonly taskIncidentService: TaskIncidentService) {}

  @Post()
  @UseGuards(ApiKeyGuard)
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({
    summary: 'Create task incidents (single or multiple images)',
    description:
      'Stores AI detections and associates them with the drone image(s). Can accept a single image or multiple images at once.',
  })
  @ApiBody({
    description: 'Payload for creating task incidents',
    schema: {
      example: [
        {
          taskId: 'TSK-ALl-01',
          severityLevel: 'High',
          imageMetadata: {
            filename: 'image_001.jpg',
            s3_bucket: 'drone-footage-bucket',
            s3_filename: 'image_001.jpg',
            imageUrl: 'https://bucket.s3.amazonaws.com/image_001.jpg',
            capture_timestamp: '2025-12-19T09:00:00Z',
            image_width: 4000,
            image_height: 3000,
            drone_model: 'DJI Phantom 4',
            drone_altitude: 120,
          },
          detections: [
            {
              detection_id: 'DETECT001',
              bounding_box: {
                x_min: 100,
                y_min: 200,
                x_max: 400,
                y_max: 600,
                width: 300,
                height: 400,
              },
              gps_coordinates: {
                latitude: 6.5244,
                longitude: 3.3792,
                altitude: 120,
                accuracy: 2,
              },
              confidence_score: 0.95,
              area_pixels: 12000,
              area_square_meters: 50,
              waste_type: 'Plastic',
            },
          ],
          totalDetections: 1,
          totalWasteAreaPixels: 12000,
          totalWasteAreaSquareMeters: 50,
          processingDurationMs: 350,
          modelVersion: 'v1.0',
          status: 'Completed',
          errorMessage: null,
        },
      ],
    },
  })
  @ApiResponse({
    status: 201,
    description: 'Task incidents created successfully',
  })
  async createTaskIncidents(
    @Body() dto: CreateTaskIncidentDto | CreateTaskIncidentDto[],
  ): Promise<{ taskImages: TaskImage[]; incidents: Incident[] }> {
    return this.taskIncidentService.createTaskIncident(dto);
  }

  @Post(':taskId/notify-complete')
  @UseGuards(ApiKeyGuard)
  @HttpCode(HttpStatus.OK)
  @ApiOperation({
    summary: 'Notify that all task incidents for a task have been created',
    description:
      'Call this after all createTaskIncident requests for a given taskId are done. Sends the incident result ready email to the subscriber once and sets the subscriber task status to Processing.',
  })
  @ApiParam({ name: 'taskId', description: 'Subscriber flight task ID' })
  @ApiOkResponse({
    description: 'Subscriber notified successfully',
    schema: {
      example: {
        message: 'Subscriber notified successfully',
        emailSent: true,
      },
    },
  })
  async notifyTaskIncidentsComplete(@Param('taskId') taskId: string) {
    return this.taskIncidentService.notifyTaskIncidentsComplete(taskId);
  }

  @Get(':taskId')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({
    summary: 'Retrieve paginated task images by subscriber task ID',
  })
  @ApiParam({ name: 'taskId', description: 'Subscriber flight task ID' })
  @ApiQuery({
    name: 'page',
    required: false,
    type: Number,
    description: 'Page number for pagination',
    example: 1,
  })
  @ApiQuery({
    name: 'limit',
    required: false,
    type: Number,
    description: 'Number of items per page (max 50)',
    example: 10,
  })
  @ApiResponse({
    status: 200,
    description: 'Paginated list of task images',
    schema: {
      example: {
        data: [
          {
            imageId: 1,
            imageUrl:
              'https://lisavue-media-storage.s3.us-east-2.amazonaws.com/drone-svgrepo-com.svg',
          },
          {
            imageId: 2,
            imageUrl:
              'https://lisavue-media-storage.s3.us-east-2.amazonaws.com/drone-image-002.jpg',
          },
        ],
        totalIncidents: 0,
        subscriberTaskStatus: FlightTaskStatus.ASSIGNED_CREW_MEMBER,
        crewMemberTaskStatus: FlightTaskStatus.REVIEW,
        area: 'Ikeja',
        location: 'Allen Avenue',
        coordinates: {
          startPosition: { longitude: 3.3947, latitude: 6.4531 },
          endPosition: { longitude: 3.402, latitude: 6.46 },
        },
        meta: {
          totalItems: 50,
          itemCount: 10,
          itemsPerPage: 10,
          totalPages: 5,
          currentPage: 1,
        },
        message: 'Task images retrieved successfully',
      },
    },
  })
  async retrieveTaskImages(
    @Param('taskId') taskId: string,
    @Query('page', new DefaultValuePipe(1), ParseIntPipe) page: number,
    @Query('limit', new DefaultValuePipe(50), ParseIntPipe) limit: number,
  ) {
    return this.taskIncidentService.retrieveTaskImagesBySubscriberTask(taskId, {
      page,
      limit,
    });
  }

  @Get('by-image/:taskImageId')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiParam({
    name: 'taskImageId',
    description: 'Task image ID',
    example: '64fa9c2e8d9c1e0012ab3456',
  })
  @ApiOkResponse({
    description: 'Incidents retrieved successfully',
    schema: {
      example: {
        message: 'Incidents retrieved successfully',
        data: [
          {
            taskId: 'TSK-ALL-001',
            incidentId: 'INC-ALL-001',
            date: '2025-12-21T06:46:53.455Z',
            severity: 'High',
            confidenceLevel: 0.95,
            incidentType: 'Plastic',
            location: 'allen avenue',
            locationCoordinates: {
              latitude: 6.6017292,
              longitude: 3.3520211,
            },
            imageUrl:
              'https://lisavue-media-storage.s3.amazonaws.com/image-001.jpg',
          },
          {
            taskId: 'TSK-ALL-002',
            incidentId: 'INC-ALL-002',
            date: '2025-12-21T06:50:12.120Z',
            severity: 'Medium',
            confidenceLevel: 0.82,
            incidentType: 'Metal',
            location: 'ikeja',
            locationCoordinates: {
              latitude: 6.4531,
              longitude: 3.3947,
            },
            imageUrl:
              'https://lisavue-media-storage.s3.amazonaws.com/image-001.jpg',
          },
        ],
      },
    },
  })
  async retrieveIncidentsByImage(@Param('taskImageId') taskImageId: number) {
    return this.taskIncidentService.retrieveIncidentsByImage(taskImageId);
  }

  @Get('subscriber/retrieve')
  @Roles(UserRole.SUBSCRIBER)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({
    summary: 'Retrieve all subscriber incidents (paginated)',
    description:
      'Returns paginated incidents including assigned crew, location, and area.',
  })
  @ApiOkResponse({
    description: 'Paginated subscriber incidents',
    example: {
      data: [
        {
          incidentId: 'INC-ALL-001',
          wasteType: 'Plastic Waste',
          status: 'Crew Member Assigned',
          assignedCrew: 'Moshood Jaji',
          location: 'allen avenue',
          area: 'Ikeja',
        },
        {
          incidentId: 'INC-ALL-002',
          wasteType: 'Metal Scrap',
          status: 'Pending',
          assignedCrew: 'Unassigned',
          location: 'allen avenue',
          area: 'Ikeja',
        },
      ],
      message: 'Incidents fetched successfully',
      meta: {
        page: 1,
        limit: 10,
        totalPages: 1,
        totalItems: 2,
      },
    },
  })
  async retrieveSubscriberIncidents(
    @Req() req: any,
    @Query() query: RetrieveSubscriberIncidentsQuery,
    @CurrentUser() user: User,
  ) {
    return this.taskIncidentService.retrieveAllSubscriberIncidents(
      user.userId,
      query,
    );
  }
}

'''
