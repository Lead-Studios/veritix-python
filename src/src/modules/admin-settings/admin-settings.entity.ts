import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';

@Entity('admin_settings')
export class AdminSettingsEntity {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column()
  adminId: string;

  @Column({ default: true })
  emailNotifications: boolean;

  @Column({ nullable: true })
  permissions: string;

  @Column({ default: true })
  twoFactorEnabled: boolean;

  @Column({ nullable: true })
  avatar: string;

  @CreateDateColumn()
  createdAt: Date;

  @UpdateDateColumn()
  updatedAt: Date;
}
