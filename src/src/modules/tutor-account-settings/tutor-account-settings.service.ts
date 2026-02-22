import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from '../../entities/user.entity';

@Injectable()
export class TutorAccountSettingsService {
  constructor(
    @InjectRepository(User) private userRepository: Repository<User>,
  ) {}

  async getTutorSettings(tutorId: string) {
    const tutor = await this.userRepository.findOne({
      where: { id: tutorId, role: 'tutor' },
    });
    if (!tutor) throw new NotFoundException('Tutor not found');
    return tutor;
  }

  async updateTutorSettings(tutorId: string, updateData: any) {
    const tutor = await this.userRepository.findOne({
      where: { id: tutorId, role: 'tutor' },
    });
    if (!tutor) throw new NotFoundException('Tutor not found');

    Object.assign(tutor, updateData);
    return this.userRepository.save(tutor);
  }

  async getTutorNotificationSettings(tutorId: string) {
    const tutor = await this.getTutorSettings(tutorId);
    return { tutorId, notificationSettings: tutor.metadata?.notificationSettings || {} };
  }

  async updateTutorNotificationSettings(tutorId: string, settings: any) {
    const tutor = await this.getTutorSettings(tutorId);
    tutor.metadata = { ...tutor.metadata, notificationSettings: settings };
    return this.userRepository.save(tutor);
  }
}
