"""Auto-converted from TypeScript.
Original file: drone-management/drone-management.controller.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  Controller,
  Post,
  Body,
  UploadedFile,
  UseInterceptors,
  Get,
  Param,
  Query,
  UseGuards,
  HttpStatus,
} from '@nestjs/common';
import { DroneService } from './drone-management.service';
import { CreateDroneDto } from './dto/create-drone.dto';
import { GetDronesDto } from './dto/get-drones.dto';
import { FileInterceptor } from '@nestjs/platform-express';
import { FormDataValidationPipe } from 'src/common/pipeline/form-data-validation';
import {
  ApiTags,
  ApiOperation,
  ApiResponse,
  ApiParam,
  ApiConsumes,
  ApiBody,
} from '@nestjs/swagger';
import { Roles } from 'src/user-auth/decorators/roles.decorators';
import { UserRole } from 'src/common/enum/user-role';
import { JwtAuthGuard } from 'src/user-auth/guard/jwt.auth.guard';
import { RolesGuard } from 'src/user-auth/guard/roles.guard';
import { DroneMissionHistoryResponse } from './interface/drone-interface';

@ApiTags('Drone Management')
@Controller('api/v1/drone')
export class DroneController {
  constructor(private readonly droneService: DroneService) {}

  @Post('create')
  @ApiOperation({ summary: 'Register a new drone for a pilot' })
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    description:
      'Drone registration payload including  NCAA certification image',
    schema: {
      type: 'object',
      required: [
        'onboardingId',
        'numberOfDrones',
        'droneMake',
        'droneModel',
        'droneSerialNumber',
        'maxCameraResolution',
        'maxFlightTime',
        'numberOfBackupBattery',
        'licenseExpiryDate',
        'ncaaCertificationImage',
      ],
      properties: {
        onboardingId: { type: 'number', example: 1 },
        numberOfDrones: { type: 'number', example: 1 },
        droneMake: { type: 'string', example: 'DJI' },
        droneModel: { type: 'string', example: 'Phantom 4 Pro' },
        droneSerialNumber: { type: 'string', example: 'DJI-XYZ-12345' },
        maxCameraResolution: { type: 'string', example: '4K UHD' },
        maxFlightTime: { type: 'string', example: '30 minutes' },
        numberOfBackupBattery: { type: 'number', example: 2 },
        licenseExpiryDate: {
          type: 'string',
          format: 'date',
          example: '2025-12-31',
        },
        ncaaCertificationImage: {
          type: 'string',
          format: 'binary',
          description: 'NCAA certification image file',
        },
      },
    },
  })
  @UseInterceptors(FileInterceptor('ncaaCertificationImage'))
  async create(
    @Body(new FormDataValidationPipe(CreateDroneDto))
    createDroneDto: CreateDroneDto,
    @UploadedFile() file?: Express.Multer.File,
  ) {
    return this.droneService.createDrone(createDroneDto, file);
  }

  @Get()
  @Roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({
    summary: 'Fetch all drones with pagination, filtering, and statistics',
  })
  @ApiResponse({
    status: 200,
    description:
      'List of drones retrieved successfully with pagination and stats',
    schema: {
      example: {
        message: 'Drones retrieved successfully.',
        data: [
          {
            id: '507f1f77bcf86cd799439011',
            droneId: 'LSDR-001',
            pilot: 1,
            pilotInfo: {
              onboardingId: 1,
              firstName: 'John',
              lastName: 'Doe',
              email: 'john.doe@example.com',
              phoneNumber: '+1234567890',
              customerId: 'PLT001',
            },
            droneMake: 'DJI',
            droneModel: 'Phantom 4 Pro',
            droneSerialNumber: 'DJI-XYZ-12345',
            maxCameraResolution: '4K UHD',
            maxFlightTime: '30 minutes',
            numberOfBackupBattery: 2,
            ncaaCertificationImage: 'https://example.com/cert.jpg',
            licenseExpiryDate: '2025-12-31T00:00:00.000Z',
            status: 'active',
            distanceCovered: 150.5,
            numberOfActiveFlights: 3,
            totalFlightHours: 125.5,
            areas: ['Lagos', 'Abuja', 'Port Harcourt'],
            createdAt: '2024-01-01T00:00:00.000Z',
            updatedAt: '2024-01-01T00:00:00.000Z',
          },
        ],
        pagination: {
          currentPage: 1,
          totalPages: 5,
          totalItems: 50,
          itemsPerPage: 10,
        },
        totalCount: 50,
        filteredCount: 50,
        stats: {
          totalDrones: 50,
          activeDrones: 30,
          underMaintenanceDrones: 5,
          totalDistanceCovered: 7500.5,
        },
      },
    },
  })
  async getAllDrones(@Query() filters: GetDronesDto) {
    return this.droneService.getAllDrones(filters);
  }

  @Get(':id')
  @Roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({ summary: 'Fetch a single drone by ID' })
  @ApiParam({
    name: 'id',
    description: 'Unique drone ID (MongoDB ObjectId)',
    example: '507f1f77bcf86cd799439011',
  })
  @ApiResponse({
    status: 200,
    description: 'Drone retrieved successfully',
    schema: {
      example: {
        message: 'Drone retrieved successfully.',
        data: {
          id: '507f1f77bcf86cd799439011',
          droneId: 'LSDR-001',
          pilot: 1,
          pilotInfo: {
            onboardingId: 1,
            firstName: 'John',
            lastName: 'Doe',
            email: 'john.doe@example.com',
            phoneNumber: '+1234567890',
            customerId: 'PLT001',
          },
          droneMake: 'DJI',
          droneModel: 'Phantom 4 Pro',
          droneSerialNumber: 'DJI-XYZ-12345',
          maxCameraResolution: '4K UHD',
          maxFlightTime: '30 minutes',
          numberOfBackupBattery: 2,
          ncaaCertificationImage: 'https://example.com/cert.jpg',
          licenseExpiryDate: '2025-12-31T00:00:00.000Z',
          status: 'active',
          distanceCovered: 150.5,
          numberOfActiveFlights: 3,
          totalFlightHours: 125.5,
          areas: ['Lagos', 'Abuja', 'Port Harcourt'],
          createdAt: '2024-01-01T00:00:00.000Z',
          updatedAt: '2024-01-01T00:00:00.000Z',
        },
      },
    },
  })
  @ApiResponse({
    status: 404,
    description: 'Drone not found',
  })
  async getDroneById(@Param('id') id: string) {
    return this.droneService.getDroneById(id);
  }

  @Get(':droneId/missions')
  @Roles(UserRole.SUPER_ADMIN, UserRole.ADMIN)
  @UseGuards(JwtAuthGuard, RolesGuard)
  @ApiOperation({
    summary: 'Retrieve drone mission history',
    description:
      'Returns mission history, incidents, distance covered, and summary stats for a specific drone',
  })
  @ApiParam({
    name: 'droneId',
    example: 'LSDR-008',
    description: 'Unique drone identifier',
  })
  @ApiResponse({
    status: HttpStatus.OK,
    description: 'Drone mission history retrieved successfully',
    schema: {
      example: {
        droneId: 'LSDR-008',
        missions: [
          {
            droneId: 'LSDR-008',
            taskId: 'TSK-AGE-001',
            date: '2025-12-13',
            time: '08:30 AM',
            area: 'Alimosho',
            location: 'Agege',
            incidentCount: 3,
            distanceCovered: 12.5,
          },
          {
            droneId: 'LSDR-008',
            taskId: 'TSK-ALL-002',
            date: '2025-12-20',
            time: '10:15 PM',
            area: 'Ikeja',
            location: 'Allen Avenue',
            incidentCount: 1,
            distanceCovered: 8.2,
          },
        ],
        stats: {
          totalCompletedTasks: 2,
          totalIncidents: 4,
          totalDistanceCovered: 20.7,
        },
      },
    },
  })
  @ApiResponse({
    status: HttpStatus.NOT_FOUND,
    description: 'No mission history found for this drone',
    schema: {
      example: {
        statusCode: 404,
        message: 'No mission history found for this drone',
      },
    },
  })
  async retrieveDroneMissionHistory(
    @Param('droneId') droneId: string,
  ): Promise<DroneMissionHistoryResponse> {
    return this.droneService.retrieveDroneMissionHistory(droneId);
  }
}

'''
