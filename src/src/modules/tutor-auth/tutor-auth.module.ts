import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from '../../entities/user.entity';
import { TutorAuthService } from './tutor-auth.service';
import { TutorAuthController } from './tutor-auth.controller';

@Module({
  imports: [
    TypeOrmModule.forFeature([User]),
    PassportModule,
    JwtModule.register({
      secret: process.env.JWT_SECRET || 'your-secret-key',
      signOptions: { expiresIn: '24h' },
    }),
  ],
  controllers: [TutorAuthController],
  providers: [TutorAuthService],
  exports: [TutorAuthService],
})
export class TutorAuthModule {}
