import {
  Controller,
  Post,
  Body,
  UseGuards,
  Get,
  Req,
  Res,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { ApiBearerAuth, ApiTags, ApiOperation } from '@nestjs/swagger';
import { AdminAuthService } from './admin-auth.service';
import { AdminLoginDto, AdminRegisterDto, ChangePasswordDto } from './dtos/admin-auth.dto';
import { JwtAuthGuard } from '../../common/guards/jwt-auth.guard';

@ApiTags('Admin Authentication')
@Controller('auth/admin')
export class AdminAuthController {
  private readonly logger = new Logger(AdminAuthController.name);

  constructor(private readonly adminAuthService: AdminAuthService) {}

  @Post('register')
  @ApiOperation({ summary: 'Register new admin' })
  async register(@Body() dto: AdminRegisterDto, @Req() req) {
    const ipAddress = req.ip || req.connection.remoteAddress;
    return this.adminAuthService.register(dto, ipAddress);
  }

  @Post('login')
  @ApiOperation({ summary: 'Admin login' })
  async login(@Body() dto: AdminLoginDto, @Req() req) {
    const ipAddress = req.ip || req.connection.remoteAddress;
    const userAgent = req.get('user-agent');
    return this.adminAuthService.login(dto, ipAddress, userAgent);
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Admin logout' })
  async logout(@Req() req) {
    const ipAddress = req.ip || req.connection.remoteAddress;
    const adminId = req.user.sub;
    return this.adminAuthService.logout(adminId, ipAddress);
  }

  @Post('change-password')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Change admin password' })
  async changePassword(@Body() dto: ChangePasswordDto, @Req() req) {
    const adminId = req.user.sub;
    return this.adminAuthService.changePassword(adminId, dto);
  }

  @Get('profile')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth()
  @ApiOperation({ summary: 'Get admin profile' })
  async getProfile(@Req() req) {
    return req.user;
  }
}
