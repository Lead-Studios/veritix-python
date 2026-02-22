import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AdminAuthController } from './admin-auth.controller';
import { AdminAuthService } from './admin-auth.service';
import { AdminAuthLog, AdminSession } from './entities/admin-auth.entity';
import { User } from '../../common/entities/user.entity';
import { AuthService } from '../../common/services/auth.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([AdminAuthLog, AdminSession, User]),
    PassportModule,
    JwtModule.register({
      secret: process.env.JWT_SECRET || 'admin-secret',
      signOptions: { expiresIn: '24h' },
    }),
  ],
  controllers: [AdminAuthController],
  providers: [AdminAuthService, AuthService],
  exports: [AdminAuthService, AuthService],
})
export class AdminAuthModule {}
