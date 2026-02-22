import { Entity, Column } from 'typeorm';
import { BaseEntity } from 'src/entities/base.entity';

// Issue 03: Order Management - Track customer orders with status
@Entity('issue_03_orders')
export class Issue03Order extends BaseEntity {
  @Column({ type: 'varchar', length: 255 })
  orderNumber: string;

  @Column({ type: 'varchar', length: 255 })
  customerId: string;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  totalAmount: number;

  @Column({ type: 'varchar', length: 50, default: 'pending' })
  status: string;

  @Column({ type: 'text' })
  items: string;

  @Column({ type: 'varchar', length: 255 })
  shippingAddress: string;

  @Column({ type: 'timestamp', nullable: true })
  shippedDate: Date;

  @Column({ type: 'timestamp', nullable: true })
  deliveredDate: Date;
}
