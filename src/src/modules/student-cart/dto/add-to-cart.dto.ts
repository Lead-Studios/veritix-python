import { IsString, IsNumber, IsOptional, Min } from 'class-validator';

export class AddToCartDto {
  @IsString()
  courseId: string;

  @IsNumber()
  @IsOptional()
  @Min(0)
  price?: number;

  @IsNumber()
  @IsOptional()
  @Min(1)
  quantity?: number;
}
