import { Entity, Column } from 'typeorm';
import { BaseEntity } from 'src/entities/base.entity';

// Issue 02: Product Catalog - Manage product inventory with categories
@Entity('issue_02_products')
export class Issue02Product extends BaseEntity {
  @Column({ type: 'varchar', length: 255 })
  name: string;

  @Column({ type: 'text' })
  description: string;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price: number;

  @Column({ type: 'integer', default: 0 })
  stock: number;

  @Column({ type: 'varchar', length: 100 })
  category: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  imageUrl: string;

  @Column({ type: 'varchar', length: 50, default: 'active' })
  status: string;

  @Column({ type: 'float', default: 0 })
  rating: number;
}
