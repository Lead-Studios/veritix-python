import { IsString, IsNumber, IsOptional, Min, MinLength } from 'class-validator';

export class CreateIssue02Dto {
  @IsString()
  @MinLength(3)
  name: string;

  @IsString()
  description: string;

  @IsNumber()
  @Min(0)
  price: number;

  @IsNumber()
  @Min(0)
  stock: number;

  @IsString()
  category: string;

  @IsOptional()
  @IsString()
  imageUrl?: string;
}

export class UpdateIssue02Dto {
  @IsOptional()
  @IsString()
  name?: string;

  @IsOptional()
  @IsString()
  description?: string;

  @IsOptional()
  @IsNumber()
  price?: number;

  @IsOptional()
  @IsNumber()
  stock?: number;

  @IsOptional()
  @IsString()
  category?: string;

  @IsOptional()
  @IsString()
  imageUrl?: string;

  @IsOptional()
  @IsString()
  status?: string;
}
