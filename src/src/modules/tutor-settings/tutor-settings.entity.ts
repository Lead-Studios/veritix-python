import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('tutor_settings')
export class TutorSettingsEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  tutorId: string;

  @Column({ nullable: true })
  bio: string;

  @Column({ nullable: true })
  specializations: string;

  @Column({ default: true })
  emailNotifications: boolean;

  @Column({ default: true })
  smsNotifications: boolean;

  @Column({ nullable: true })
  timezone: string;

  @Column({ default: 50 })
  hourlyRate: number;

  @Column({ default: true })
  isAvailable: boolean;

  @Column({ nullable: true })
  avatar: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
