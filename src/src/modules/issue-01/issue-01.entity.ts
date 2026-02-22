import { Entity, Column } from 'typeorm';
import { BaseEntity } from 'src/entities/base.entity';

// Issue 01: User Profile Management - Store user profile data with validation
@Entity('issue_01_user_profiles')
export class Issue01UserProfile extends BaseEntity {
  @Column({ type: 'varchar', length: 255 })
  firstName: string;

  @Column({ type: 'varchar', length: 255 })
  lastName: string;

  @Column({ type: 'varchar', length: 255, unique: true })
  email: string;

  @Column({ type: 'varchar', length: 20 })
  phone: string;

  @Column({ type: 'text', nullable: true })
  bio: string;

  @Column({ type: 'varchar', length: 255, nullable: true })
  profileImageUrl: string;

  @Column({ type: 'varchar', length: 50, default: 'active' })
  status: string;
}
