"""Auto-converted from TypeScript.
Original file: crew-member-task/helper/subscriber-task-email-function.ts
The original TypeScript source is kept below for reference.
"""

from __future__ import annotations

TS_SOURCE = r'''
import {
  Injectable,
  InternalServerErrorException,
  Logger,
} from '@nestjs/common';
import { EmailService } from '../../config/email/email.service';

@Injectable()
export class SubscriberTaskEmailFunction {
  private readonly logger = new Logger(SubscriberTaskEmailFunction.name);

  constructor(private readonly emailService: EmailService) {}

  async sendTaskAcceptedEmail(
    to: string,
    subscriberFirstName: string,
    crewMemberName: string,
    taskId: string,
    location: string,
    dueDate: string,
    dueTime: string,
  ) {
    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'subscriber-crew-task-accepted-email',
      );

      const placeholders = {
        subscriberFirstName: subscriberFirstName,
        crewMemberName: crewMemberName,
        taskId: taskId,
        location: location,
        dueDate: dueDate,
        dueTime: dueTime,
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'Task Accepted by Crew Member - Lisavue',
        htmlContent,
      );

      this.logger.log(
        `Subscriber task accepted email sent successfully to ${to}`,
      );
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(
        `Error sending subscriber task accepted email to ${to}: ${errMessage}`,
      );
      throw new InternalServerErrorException(
        'Error in sending subscriber task accepted email',
      );
    }
  }

  async sendTaskRejectedEmail(
    to: string,
    subscriberFirstName: string,
    crewMemberName: string,
    taskId: string,
    location: string,
    dueDate: string,
    rejectionReason: string,
  ) {
    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'subscriber-crew-task-rejected-email',
      );

      const placeholders = {
        subscriberFirstName: subscriberFirstName,
        crewMemberName: crewMemberName,
        taskId: taskId,
        location: location,
        dueDate: dueDate,
        rejectionReason: rejectionReason || 'No reason provided',
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'Task Rejected by Crew Member - Lisavue',
        htmlContent,
      );

      this.logger.log(
        `Subscriber task rejected email sent successfully to ${to}`,
      );
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(
        `Error sending subscriber task rejected email to ${to}: ${errMessage}`,
      );
      throw new InternalServerErrorException(
        'Error in sending subscriber task rejected email',
      );
    }
  }

  async sendTaskStoppedEmail(
    to: string,
    subscriberFirstName: string,
    crewMemberName: string,
    taskId: string,
    location: string,
    dueDate: string,
    stoppedReason: string,
  ) {
    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'subscriber-crew-task-stopped-email',
      );

      const placeholders = {
        subscriberFirstName: subscriberFirstName,
        crewMemberName: crewMemberName,
        taskId: taskId,
        location: location,
        dueDate: dueDate,
        stoppedReason: stoppedReason || 'No reason provided',
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'Task Stopped by Crew Member - Lisavue',
        htmlContent,
      );

      this.logger.log(
        `Subscriber task stopped email sent successfully to ${to}`,
      );
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(
        `Error sending subscriber task stopped email to ${to}: ${errMessage}`,
      );
      throw new InternalServerErrorException(
        'Error in sending subscriber task stopped email',
      );
    }
  }

  async sendTaskCompletedEmail(
    to: string,
    subscriberFirstName: string,
    crewMemberName: string,
    taskId: string,
    location: string,
    dueDate: string,
    evidenceCount: number,
  ) {
    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'subscriber-crew-task-completed-email',
      );

      const placeholders = {
        subscriberFirstName: subscriberFirstName,
        crewMemberName: crewMemberName,
        taskId: taskId,
        location: location,
        dueDate: dueDate,
        evidenceCount: evidenceCount.toString(),
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'Task Completed by Crew Member - Lisavue',
        htmlContent,
      );

      this.logger.log(
        `Subscriber task completed email sent successfully to ${to}`,
      );
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(
        `Error sending subscriber task completed email to ${to}: ${errMessage}`,
      );
      throw new InternalServerErrorException(
        'Error in sending subscriber task completed email',
      );
    }
  }

  async sendCrewMemberTaskAssignedEmail(
    to: string,
    firstName: string,
    taskId: string,
    location: string,
    dueDate: string,
    dueTime: string,
    priority: string,
    note?: string,
  ) {
    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'crew-member-task-assigned-email',
      );

      const noteSection = note
        ? `<p style="margin: 5px 0"><strong>Note:</strong> ${note}</p>`
        : '';

      const placeholders = {
        firstName: firstName,
        taskId: taskId,
        location: location,
        dueDate: dueDate,
        dueTime: dueTime,
        priority: priority,
        note: noteSection,
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'New Task Assigned - Lisavue',
        htmlContent,
      );

      this.logger.log(
        `Crew member task assigned email sent successfully to ${to}`,
      );
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(
        `Error sending crew member task assigned email to ${to}: ${errMessage}`,
      );
      throw new InternalServerErrorException(
        'Error in sending crew member task assigned email',
      );
    }
  }
}

'''
