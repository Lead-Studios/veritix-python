import { Controller, Post, Body, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { StudentAuthService } from './student-auth.service';
import { CreateStudentDto } from './dto/create-student.dto';
import { LoginStudentDto } from './dto/login-student.dto';
import { ResetPasswordDto } from './dto/reset-password.dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';

@ApiTags('Student Authentication')
@Controller('student')
export class StudentAuthController {
  constructor(private readonly authService: StudentAuthService) {}

  @Post('create')
  @ApiOperation({ summary: 'Create a new student account' })
  async register(@Body() createStudentDto: CreateStudentDto) {
    return this.authService.register(createStudentDto);
  }

  @Post('verify-email')
  @ApiOperation({ summary: 'Verify student email address' })
  async verifyEmail(@Body('email') email: string) {
    return this.authService.verifyEmail(email);
  }

  @Post('login')
  @ApiOperation({ summary: 'Sign in student with email and password' })
  async login(@Body() loginStudentDto: LoginStudentDto) {
    return this.authService.login(loginStudentDto);
  }

  @Post('forget/password')
  @ApiOperation({ summary: 'Initiate forgot password flow' })
  async forgotPassword(@Body('email') email: string) {
    return this.authService.forgotPassword(email);
  }

  @Post('reset/password')
  @ApiOperation({ summary: "Reset student's password" })
  async resetPassword(@Body() resetPasswordDto: ResetPasswordDto) {
    return this.authService.resetPassword(resetPasswordDto);
  }

  @Post('refresh-token')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: "Refresh student's token" })
  async refreshToken(@Request() req) {
    return this.authService.refreshToken(req.user.userId);
  }
}
