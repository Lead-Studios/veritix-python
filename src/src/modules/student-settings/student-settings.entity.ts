import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('student_settings')
export class StudentSettingsEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  studentId: string;

  @Column({ default: true })
  emailNotifications: boolean;

  @Column({ default: true })
  courseReminders: boolean;

  @Column({ default: true })
  pushNotifications: boolean;

  @Column({ nullable: true })
  preferredLanguage: string;

  @Column({ nullable: true })
  timezone: string;

  @Column({ default: false })
  displayProfile: boolean;

  @Column({ nullable: true })
  bio: string;

  @Column({ nullable: true })
  avatar: string;

  @Column({ default: false })
  twoFactorEnabled: boolean;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
