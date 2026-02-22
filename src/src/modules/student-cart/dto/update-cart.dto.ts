import { IsNumber, IsOptional, Min } from 'class-validator';

export class UpdateCartDto {
  @IsNumber()
  @IsOptional()
  @Min(0)
  price?: number;

  @IsNumber()
  @IsOptional()
  @Min(1)
  quantity?: number;
}
