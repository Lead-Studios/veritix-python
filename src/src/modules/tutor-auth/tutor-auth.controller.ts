import { Controller, Post, Get, Patch, Body, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { TutorAuthService } from './tutor-auth.service';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { Roles } from '../../auth/decorators/roles.decorator';
import { RolesGuard } from '../../auth/guards/roles.guard';

@ApiTags('Tutor Authentication')
@Controller('tutor/auth')
export class TutorAuthController {
  constructor(private readonly authService: TutorAuthService) {}

  @Post('register')
  @ApiOperation({ summary: 'Register a new tutor' })
  async register(@Body() body: { email: string; password: string; firstName: string; lastName: string }) {
    return this.authService.registerTutor(body.email, body.password, body.firstName, body.lastName);
  }

  @Post('login')
  @ApiOperation({ summary: 'Tutor login' })
  async login(@Body() body: { email: string; password: string }) {
    return this.authService.loginTutor(body.email, body.password);
  }

  @Get('profile')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('tutor')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get tutor profile' })
  async getProfile(@Request() req) {
    return this.authService.getTutorProfile(req.user.userId);
  }

  @Patch('profile')
  @UseGuards(JwtAuthGuard, RolesGuard)
  @Roles('tutor')
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Update tutor profile' })
  async updateProfile(@Body() updateData: any, @Request() req) {
    return this.authService.updateTutorProfile(req.user.userId, updateData);
  }
}
