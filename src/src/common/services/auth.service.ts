import { Injectable, UnauthorizedException, BadRequestException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';

@Injectable()
export class AuthService {
  constructor(private jwtService: JwtService) {}

  async hashPassword(password: string): Promise<string> {
    const salt = await bcrypt.genSalt(10);
    return bcrypt.hash(password, salt);
  }

  async validatePassword(
    providedPassword: string,
    storedHash: string,
  ): Promise<boolean> {
    return bcrypt.compare(providedPassword, storedHash);
  }

  generateAccessToken(payload: any): string {
    return this.jwtService.sign(payload, {
      expiresIn: process.env.JWT_EXPIRATION || '3600s',
    });
  }

  generateRefreshToken(payload: any): string {
    return this.jwtService.sign(payload, {
      expiresIn: '7d',
    });
  }

  verifyToken(token: string): any {
    try {
      return this.jwtService.verify(token);
    } catch (error) {
      throw new UnauthorizedException('Invalid or expired token');
    }
  }

  decodeToken(token: string): any {
    return this.jwtService.decode(token);
  }

  generateTokens(payload: any) {
    return {
      accessToken: this.generateAccessToken(payload),
      refreshToken: this.generateRefreshToken(payload),
    };
  }

  validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  validatePasswordStrength(password: string): {
    isValid: boolean;
    message?: string;
  } {
    if (password.length < 8) {
      return { isValid: false, message: 'Password must be at least 8 characters' };
    }

    if (!/[A-Z]/.test(password)) {
      return { isValid: false, message: 'Password must contain uppercase letter' };
    }

    if (!/[a-z]/.test(password)) {
      return { isValid: false, message: 'Password must contain lowercase letter' };
    }

    if (!/[0-9]/.test(password)) {
      return { isValid: false, message: 'Password must contain number' };
    }

    return { isValid: true };
  }
}
