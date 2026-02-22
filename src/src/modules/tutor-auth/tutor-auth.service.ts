import { Injectable, BadRequestException, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcrypt';
import { User } from '../../entities/user.entity';

@Injectable()
export class TutorAuthService {
  constructor(
    @InjectRepository(User) private userRepository: Repository<User>,
    private jwtService: JwtService,
  ) {}

  async registerTutor(email: string, password: string, firstName: string, lastName: string) {
    const existingUser = await this.userRepository.findOne({ where: { email } });
    if (existingUser) {
      throw new BadRequestException('Email already registered');
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    const tutor = this.userRepository.create({
      email,
      password: hashedPassword,
      firstName,
      lastName,
      role: 'tutor',
      emailVerified: true,
    });

    await this.userRepository.save(tutor);
    return { message: 'Tutor registered successfully', userId: tutor.id };
  }

  async loginTutor(email: string, password: string) {
    const user = await this.userRepository.findOne({ where: { email, role: 'tutor' } });
    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const token = this.jwtService.sign({
      sub: user.id,
      email: user.email,
      role: user.role,
    });

    return { accessToken: token, user: { id: user.id, email: user.email, role: user.role } };
  }

  async getTutorProfile(tutorId: string) {
    const tutor = await this.userRepository.findOne({ where: { id: tutorId, role: 'tutor' } });
    if (!tutor) {
      throw new BadRequestException('Tutor not found');
    }
    return tutor;
  }

  async updateTutorProfile(tutorId: string, updateData: Partial<User>) {
    const tutor = await this.userRepository.findOne({ where: { id: tutorId, role: 'tutor' } });
    if (!tutor) {
      throw new BadRequestException('Tutor not found');
    }

    Object.assign(tutor, updateData);
    await this.userRepository.save(tutor);
    return tutor;
  }
}
