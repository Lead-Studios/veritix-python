import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AddToCartDto } from './dto/add-to-cart.dto';
import { StudentCart } from './entities/student-cart.entity';
import { UpdateCartDto } from './dto/update-cart.dto';

@Injectable()
export class StudentCartService {
  constructor(
    @InjectRepository(StudentCart) private cartRepository: Repository<StudentCart>,
  ) {}

  async addCourseToCart(studentId: string, addToCartDto: AddToCartDto) {
    const { courseId } = addToCartDto;

    let cartItem = await this.cartRepository.findOne({
      where: { studentId, courseId },
    });

    if (!cartItem) {
      cartItem = this.cartRepository.create({
        studentId,
        courseId,
      });
      await this.cartRepository.save(cartItem);
    }

    return { message: 'Course added to cart', cartItem };
  }

  async getStudentCart(studentId: string) {
    const cartItems = await this.cartRepository.find({
      where: { studentId },
    });

    return { cartItems, total: cartItems.length };
  }

  async updateCart(studentId: string, cartId: string, updateCartDto: UpdateCartDto) {
    const cartItem = await this.cartRepository.findOne({
      where: { id: cartId, studentId },
    });

    if (!cartItem) {
      throw new NotFoundException('Cart item not found');
    }

    Object.assign(cartItem, updateCartDto);
    await this.cartRepository.save(cartItem);

    return { message: 'Cart updated', cartItem };
  }

  async removeFromCart(studentId: string, cartId: string) {
    const cartItem = await this.cartRepository.findOne({
      where: { id: cartId, studentId },
    });

    if (!cartItem) {
      throw new NotFoundException('Cart item not found');
    }

    await this.cartRepository.remove(cartItem);
    return { message: 'Course removed from cart' };
  }
}
