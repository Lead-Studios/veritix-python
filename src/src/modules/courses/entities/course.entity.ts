import {
  Entity,
  Column,
  PrimaryGeneratedColumn,
  ManyToOne,
  JoinColumn,
  OneToMany,
  CreateDateColumn,
  UpdateDateColumn,
} from 'typeorm';
import { User } from '../../../common/entities/user.entity';

export enum CourseLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
}

export enum CourseStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

@Entity('courses')
export class Course {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar' })
  title: string;

  @Column({ type: 'text' })
  description: string;

  @Column({ type: 'varchar' })
  category: string;

  @Column({
    type: 'enum',
    enum: CourseLevel,
    default: CourseLevel.BEGINNER,
  })
  level: CourseLevel;

  @Column({ type: 'decimal', precision: 10, scale: 2 })
  price: number;

  @Column({ type: 'int' })
  duration: number; // in hours

  @Column('uuid')
  tutorId: string;

  @ManyToOne(() => User)
  @JoinColumn({ name: 'tutorId' })
  tutor: User;

  @Column({ type: 'varchar', nullable: true })
  imageUrl: string;

  @Column({
    type: 'enum',
    enum: CourseStatus,
    default: CourseStatus.DRAFT,
  })
  status: CourseStatus;

  @Column({ type: 'int', default: 0 })
  enrollmentCount: number;

  @Column({ type: 'decimal', precision: 3, scale: 2, default: 0 })
  averageRating: number;

  @Column({ type: 'int', default: 0 })
  ratingCount: number;

  @Column({ type: 'text', nullable: true })
  prerequisites: string;

  @Column({ type: 'text', nullable: true })
  learningOutcomes: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
