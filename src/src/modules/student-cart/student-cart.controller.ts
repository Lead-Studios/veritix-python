import { Controller, Post, Get, Patch, Delete, Body, Param, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiBearerAuth } from '@nestjs/swagger';
import { StudentCartService } from './student-cart.service';
import { AddToCartDto } from './dto/add-to-cart.dto';
import { UpdateCartDto } from './dto/update-cart.dto';
import { JwtAuthGuard } from '../../auth/guards/jwt-auth.guard';
import { Roles } from '../../auth/decorators/roles.decorator';
import { RolesGuard } from '../../auth/guards/roles.guard';

@ApiTags('Student Cart')
@Controller('student/cart')
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('student')
@ApiBearerAuth()
export class StudentCartController {
  constructor(private readonly cartService: StudentCartService) {}

  @Post(':id/add')
  @ApiOperation({ summary: 'Add course to student cart' })
  async addToCart(
    @Param('id') studentId: string,
    @Body() addToCartDto: AddToCartDto,
    @Request() req,
  ) {
    return this.cartService.addCourseToCart(req.user.userId, addToCartDto);
  }

  @Get()
  @ApiOperation({ summary: 'Retrieve student cart' })
  async getCart(@Request() req) {
    return this.cartService.getStudentCart(req.user.userId);
  }

  @Patch(':id/cart')
  @ApiOperation({ summary: 'Update student cart' })
  async updateCart(
    @Param('id') studentId: string,
    @Body() updateCartDto: UpdateCartDto,
    @Request() req,
  ) {
    return this.cartService.updateCart(req.user.userId, studentId, updateCartDto);
  }

  @Delete(':id/cart')
  @ApiOperation({ summary: 'Remove course from cart' })
  async removeFromCart(@Param('id') cartId: string, @Request() req) {
    return this.cartService.removeFromCart(req.user.userId, cartId);
  }
}
