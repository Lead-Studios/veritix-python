import {
  Injectable,
  BadRequestException,
  UnauthorizedException,
  Logger,
  ConflictException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { JwtService } from '@nestjs/jwt';
import { User } from '../../common/entities/user.entity';
import { AuthService } from '../../common/services/auth.service';
import { AdminLoginDto, AdminRegisterDto, ChangePasswordDto } from './dtos/admin-auth.dto';
import { AdminAuthLog, AdminSession } from './entities/admin-auth.entity';

@Injectable()
export class AdminAuthService {
  private readonly logger = new Logger(AdminAuthService.name);

  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
    @InjectRepository(AdminAuthLog)
    private authLogsRepository: Repository<AdminAuthLog>,
    @InjectRepository(AdminSession)
    private sessionsRepository: Repository<AdminSession>,
    private authService: AuthService,
    private jwtService: JwtService,
  ) {}

  async register(dto: AdminRegisterDto, ipAddress: string) {
    try {
      // Check if admin already exists
      const existingAdmin = await this.usersRepository.findOne({
        where: { email: dto.email },
      });

      if (existingAdmin) {
        throw new ConflictException('Admin with this email already exists');
      }

      // Validate password strength
      const passwordValidation = this.authService.validatePasswordStrength(
        dto.password,
      );
      if (!passwordValidation.isValid) {
        throw new BadRequestException(passwordValidation.message);
      }

      // Hash password
      const hashedPassword = await this.authService.hashPassword(dto.password);

      // Create admin user
      const admin = this.usersRepository.create({
        email: dto.email,
        password: hashedPassword,
        firstName: dto.firstName,
        lastName: dto.lastName,
        role: 'admin',
        isActive: true,
        isEmailVerified: true,
      });

      await this.usersRepository.save(admin);

      this.logger.log(`Admin registered: ${admin.email}`);

      // Log the registration
      await this.logAuthEvent(admin.id, 'register', ipAddress, true);

      return {
        id: admin.id,
        email: admin.email,
        firstName: admin.firstName,
        lastName: admin.lastName,
        role: admin.role,
      };
    } catch (error) {
      this.logger.error(`Registration failed: ${error.message}`);
      throw error;
    }
  }

  async login(dto: AdminLoginDto, ipAddress: string, userAgent: string) {
    try {
      // Find admin by email
      const admin = await this.usersRepository.findOne({
        where: { email: dto.email, role: 'admin' },
      });

      if (!admin) {
        await this.logAuthEvent(null, 'login', ipAddress, false, 'User not found');
        throw new UnauthorizedException('Invalid credentials');
      }

      if (!admin.isActive) {
        throw new UnauthorizedException('Admin account is inactive');
      }

      // Validate password
      const isPasswordValid = await this.authService.validatePassword(
        dto.password,
        admin.password,
      );

      if (!isPasswordValid) {
        await this.logAuthEvent(admin.id, 'login', ipAddress, false, 'Invalid password');
        throw new UnauthorizedException('Invalid credentials');
      }

      // Generate tokens
      const tokens = this.authService.generateTokens({
        sub: admin.id,
        email: admin.email,
        role: admin.role,
      });

      // Create session
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + 7); // 7 days

      await this.sessionsRepository.save({
        adminId: admin.id,
        refreshToken: tokens.refreshToken,
        ipAddress,
        expiresAt,
      });

      // Update last login
      admin.lastLoginAt = new Date();
      await this.usersRepository.save(admin);

      // Log successful login
      await this.logAuthEvent(admin.id, 'login', ipAddress, true);

      this.logger.log(`Admin logged in: ${admin.email}`);

      return {
        id: admin.id,
        email: admin.email,
        firstName: admin.firstName,
        lastName: admin.lastName,
        role: admin.role,
        ...tokens,
      };
    } catch (error) {
      this.logger.error(`Login failed: ${error.message}`);
      throw error;
    }
  }

  async logout(adminId: string, ipAddress: string) {
    try {
      // Invalidate all sessions for this admin
      await this.sessionsRepository.update(
        { adminId, isActive: true },
        { isActive: false },
      );

      await this.logAuthEvent(adminId, 'logout', ipAddress, true);

      this.logger.log(`Admin logged out: ${adminId}`);

      return { message: 'Logged out successfully' };
    } catch (error) {
      this.logger.error(`Logout failed: ${error.message}`);
      throw error;
    }
  }

  async changePassword(adminId: string, dto: ChangePasswordDto) {
    try {
      const admin = await this.usersRepository.findOne(adminId);

      if (!admin) {
        throw new UnauthorizedException('Admin not found');
      }

      // Validate current password
      const isPasswordValid = await this.authService.validatePassword(
        dto.currentPassword,
        admin.password,
      );

      if (!isPasswordValid) {
        throw new UnauthorizedException('Current password is incorrect');
      }

      // Validate new password strength
      const passwordValidation = this.authService.validatePasswordStrength(
        dto.newPassword,
      );
      if (!passwordValidation.isValid) {
        throw new BadRequestException(passwordValidation.message);
      }

      // Update password
      admin.password = await this.authService.hashPassword(dto.newPassword);
      await this.usersRepository.save(admin);

      this.logger.log(`Password changed for admin: ${adminId}`);

      return { message: 'Password changed successfully' };
    } catch (error) {
      this.logger.error(`Change password failed: ${error.message}`);
      throw error;
    }
  }

  private async logAuthEvent(
    adminId: string | null,
    action: string,
    ipAddress: string,
    isSuccessful: boolean,
    errorMessage?: string,
  ) {
    try {
      await this.authLogsRepository.save({
        adminId,
        action,
        ipAddress,
        isSuccessful,
        errorMessage,
      });
    } catch (error) {
      this.logger.error(`Failed to log auth event: ${error.message}`);
    }
  }
}
