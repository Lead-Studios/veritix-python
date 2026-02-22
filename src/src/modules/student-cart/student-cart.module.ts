import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { StudentCartService } from './student-cart.service';
import { StudentCartController } from './student-cart.controller';
import { StudentCart } from './entities/student-cart.entity';

@Module({
  imports: [TypeOrmModule.forFeature([StudentCart])],
  controllers: [StudentCartController],
  providers: [StudentCartService],
  exports: [StudentCartService],
})
export class StudentCartModule {}
