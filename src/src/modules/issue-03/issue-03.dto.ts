import { IsString, IsNumber, IsOptional, IsArray, Min } from 'class-validator';

export class CreateIssue03Dto {
  @IsString()
  orderNumber: string;

  @IsString()
  customerId: string;

  @IsNumber()
  @Min(0)
  totalAmount: number;

  @IsArray()
  items: string[];

  @IsString()
  shippingAddress: string;
}

export class UpdateIssue03Dto {
  @IsOptional()
  @IsString()
  status?: string;

  @IsOptional()
  @IsNumber()
  totalAmount?: number;

  @IsOptional()
  @IsString()
  shippingAddress?: string;
}
