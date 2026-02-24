"""Auto-converted from TypeScript.
Original file: crew-member-task/gateway/crew-member-location.gateway.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayInit,
  OnGatewayConnection,
  OnGatewayDisconnect,
  ConnectedSocket,
  MessageBody,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger } from '@nestjs/common';
import { CrewMemberLocationService } from '../crew-member-location.service';
import { UpdateLocationDto } from '../dto/update-location.dto';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';

@WebSocketGateway({
  cors: {
    origin: '*',
    credentials: true,
  },
  namespace: '/location',
  transports: ['websocket', 'polling'],
  pingTimeout: 60000,
  pingInterval: 25000,
  upgradeTimeout: 30000,
  allowEIO3: true,
})
export class CrewMemberLocationGateway
  implements OnGatewayInit, OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer() server: Server;
  private logger = new Logger('CrewMemberLocationGateway');
  private connectedUsers = new Map<string, any>();

  constructor(
    private readonly locationService: CrewMemberLocationService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
  ) {}

  afterInit(server: Server) {
    this.logger.log('WebSocket Location Gateway initialized');
  }

  async handleConnection(client: Socket) {
    try {
      const token =
        client.handshake.auth?.token ||
        client.handshake.query?.token ||
        (typeof client.handshake.query?.token === 'string'
          ? client.handshake.query.token
          : Array.isArray(client.handshake.query?.token)
            ? client.handshake.query.token[0]
            : null) ||
        client.handshake.headers?.authorization?.replace('Bearer ', '') ||
        client.handshake.headers?.auth;

      if (!token) {
        this.logger.warn(`Connection rejected: No token provided`);
        client.disconnect();
        return;
      }

      const decoded = this.jwtService.verify(token, {
        secret: this.configService.get('ACCESS_TOKEN_SECRET'),
      });

      this.connectedUsers.set(client.id, {
        crewMemberId: decoded.crewMemberId,
        subscriberId: decoded.subscriberId,
        taskId: null,
      });

      this.logger.log(
        `Crew member ${decoded.crewMemberId} connected (socket: ${client.id})`,
      );

      client.emit('connection_established', {
        message: 'Connected to location tracking service',
        socketId: client.id,
      });
    } catch (error) {
      this.logger.error(`Connection error: ${error.message}`);
      client.disconnect();
    }
  }

  async handleDisconnect(client: Socket) {
    const userData = this.connectedUsers.get(client.id);
    if (userData && userData.taskId) {
      await this.locationService.deleteLocationForTask(
        userData.crewMemberId,
        userData.taskId,
      );
    }
    this.connectedUsers.delete(client.id);
  }

  @SubscribeMessage('stop_tracking')
  async handleStopTracking(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { taskId: string },
  ) {
    const userData = this.connectedUsers.get(client.id);

    if (!userData) {
      client.emit('error', { message: 'User not authenticated' });
      return;
    }

    try {
      await this.locationService.deleteLocationForTask(
        userData.crewMemberId,
        data.taskId,
      );

      this.logger.log(
        `Tracking stopped and location deleted for crew member ${userData.crewMemberId}, task ${data.taskId}`,
      );

      client.emit('tracking_stopped', {
        message: 'Location tracking stopped',
        taskId: data.taskId,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      this.logger.error(`Error stopping tracking: ${error.message}`);
      client.emit('error', {
        message: 'Failed to stop tracking',
        error: error.message,
      });
    }
  }

  @SubscribeMessage('share_location')
  async handleInitialLocation(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: UpdateLocationDto & { taskId: string },
  ) {
    const userData = this.connectedUsers.get(client.id);

    if (!userData) {
      client.emit('error', { message: 'User not authenticated' });
      return;
    }

    const { taskId, latitude, longitude, accuracy, altitude, speed, heading } =
      data;

    userData.taskId = taskId;
    this.connectedUsers.set(client.id, userData);

    try {
      const locationUpdate = await this.locationService.updateLocation({
        crewMemberId: userData.crewMemberId,
        taskId,
        subscriberId: userData.subscriberId,
        latitude,
        longitude,
        accuracy,
        altitude,
        speed,
        heading,
      });

      if (!locationUpdate) {
        this.logger.error(
          `Failed to save location for crew member ${userData.crewMemberId}`,
        );
        client.emit('error', { message: 'Failed to share location' });
        return;
      }

      this.logger.log(`Location shared successfully`);

      client.emit('location_shared', {
        message: 'Location shared successfully',
        data: locationUpdate,
      });
    } catch (error) {
      this.logger.error(`Error sharing location: ${error.message}`);
      client.emit('error', {
        message: 'Failed to share location',
        error: error.message,
      });
    }
  }

  @SubscribeMessage('update_location')
  async handleLocationUpdate(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: UpdateLocationDto & { taskId: string },
  ) {
    const userData = this.connectedUsers.get(client.id);

    if (!userData) {
      client.emit('error', { message: 'User not authenticated' });
      return;
    }

    const { taskId, latitude, longitude, accuracy, altitude, speed, heading } =
      data;

    try {
      const locationUpdate = await this.locationService.updateLocation({
        crewMemberId: userData.crewMemberId,
        taskId,
        subscriberId: userData.subscriberId,
        latitude,
        longitude,
        accuracy,
        altitude,
        speed,
        heading,
      });

      if (!locationUpdate) {
        client.emit('error', { message: 'Failed to update location' });
        return;
      }

      client.emit('location_updated', {
        message: 'Location updated successfully',
        data: locationUpdate,
      });

      this.logger.log(
        `Location updated for crew member ${userData.crewMemberId}`,
      );
    } catch (error) {
      this.logger.error(`Error updating location: ${error.message}`);
      client.emit('error', {
        message: 'Failed to update location',
        error: error.message,
      });
    }
  }
}

'''
