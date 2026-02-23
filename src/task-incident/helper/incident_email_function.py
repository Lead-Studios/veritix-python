"""Auto-converted from TypeScript.
Original file: task-incident/helper/incident-email-function.ts
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
export class IncidentEmailFunctions {
  private readonly logger = new Logger(IncidentEmailFunctions.name);

  constructor(private readonly emailService: EmailService) {}

  async sendIncidentResultReadyEmail(params: {
    to: string;
    organizationName: string;
    taskId: string;
    totalIncidents: number;
    severitySummary: string;
    taskUrl: string;
  }) {
    const {
      to,
      organizationName,
      taskId,
      totalIncidents,
      severitySummary,
      taskUrl,
    } = params;

    try {
      let htmlContent = await this.emailService.loadHtmlTemplate(
        'subscriber-incident-ready-email',
      );

      const placeholders = {
        organizationName,
        taskId,
        totalIncidents: totalIncidents.toString(),
        severitySummary,
        taskUrl,
        year: new Date().getFullYear().toString(),
      };

      htmlContent = this.emailService.replacePlaceholders(
        htmlContent,
        placeholders,
      );

      await this.emailService.sendEmail(
        to,
        'Incident Detection Results Ready — Lisavue',
        htmlContent,
      );

      this.logger.log(`Incident result email sent successfully to ${to}`);
    } catch (error: unknown) {
      const errMessage = error instanceof Error ? error.message : String(error);

      this.logger.error(
        `Error sending incident result email to ${to}: ${errMessage}`,
      );

      throw new InternalServerErrorException(
        'Error in sending incident result email',
      );
    }
  }
}

'''
