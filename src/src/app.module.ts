import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { JwtModule } from '@nestjs/jwt';
import { databaseConfig } from './config/database.config';
import { AppController } from './app.controller';
import { AppService } from './app.service';

// Import all feature modules (40 issues)
import { AdminAuthModule } from './modules/admin-auth/admin-auth.module';
import { AdminSettingsModule } from './modules/admin-settings/admin-settings.module';
import { StudentSettingsModule } from './modules/student-settings/student-settings.module';
import { TutorSettingsModule } from './modules/tutor-settings/tutor-settings.module';
import { StudentAuthModule } from './modules/student-auth/student-auth.module';
import { TutorAuthModule } from './modules/tutor-auth/tutor-auth.module';
import { GoogleAuthModule } from './modules/google-auth/google-auth.module';
import { CoursePerformanceModule } from './modules/course-performance/course-performance.module';
import { CourseCategorizationModule } from './modules/course-categorization/course-categorization.module';
import { CoursesModule } from './modules/courses/courses.module';
import { AdminCoursesModule } from './modules/admin-courses/admin-courses.module';
import { TutoringSessionsModule } from './modules/tutoring-sessions/tutoring-sessions.module';
import { GamificationModule } from './modules/gamification/gamification.module';
import { CertificationModule } from './modules/certification/certification.module';
import { CourseRatingsModule } from './modules/course-ratings/course-ratings.module';
import { WishlistModule } from './modules/wishlist/wishlist.module';
import { FAQModule } from './modules/faq/faq.module';
import { TermsConditionsModule } from './modules/terms-conditions/terms-conditions.module';
import { PrivacyPolicyModule } from './modules/privacy-policy/privacy-policy.module';
import { TutorAnalyticsModule } from './modules/tutor-analytics/tutor-analytics.module';
import { StudentAnalyticsModule } from './modules/student-analytics/student-analytics.module';
import { CourseAnalyticsModule } from './modules/course-analytics/course-analytics.module';
import { CertificateSharingModule } from './modules/certificate-sharing/certificate-sharing.module';
import { CertificateManagementModule } from './modules/certificate-management/certificate-management.module';
import { CertificateReviewModule } from './modules/certificate-review/certificate-review.module';
import { CertificateRequestModule } from './modules/certificate-request/certificate-request.module';
import { FinancialAidModule } from './modules/financial-aid/financial-aid.module';
import { AidApplicationModule } from './modules/aid-application/aid-application.module';
import { AboutSectionModule } from './modules/about-section/about-section.module';
import { ContactMessagesModule } from './modules/contact-messages/contact-messages.module';
import { BadgesNFTModule } from './modules/badges-nft/badges-nft.module';
import { NotificationsModule } from './modules/notifications/notifications.module';
import { OrganizationsModule } from './modules/organizations/organizations.module';
import { OrganizationMembersModule } from './modules/organization-members/organization-members.module';
import { PointsManagementModule } from './modules/points-management/points-management.module';
import { RemovalRequestsModule } from './modules/removal-requests/removal-requests.module';
import { ReportAbuseModule } from './modules/report-abuse/report-abuse.module';
import { SessionManagementModule } from './modules/session-management/session-management.module';
import { SubscriptionsModule } from './modules/subscriptions/subscriptions.module';
import { CartModule } from './modules/cart/cart.module';
import { SavedCoursesModule } from './modules/saved-courses/saved-courses.module';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    TypeOrmModule.forRoot(databaseConfig()),
    JwtModule.register({
      secret: process.env.JWT_SECRET || 'your_jwt_secret_key',
      signOptions: { expiresIn: process.env.JWT_EXPIRATION || '3600' },
    }),
    // Authentication & Settings Modules
    AdminAuthModule,
    StudentAuthModule,
    TutorAuthModule,
    GoogleAuthModule,
    AdminSettingsModule,
    StudentSettingsModule,
    TutorSettingsModule,
    
    // Course Management Modules
    CoursesModule,
    AdminCoursesModule,
    CoursePerformanceModule,
    CourseCategorizationModule,
    CourseRatingsModule,
    CourseAnalyticsModule,
    
    // Learning & Sessions
    TutoringSessionsModule,
    SessionManagementModule,
    
    // Gamification & Rewards
    GamificationModule,
    PointsManagementModule,
    BadgesNFTModule,
    
    // Certifications & Achievements
    CertificationModule,
    CertificateManagementModule,
    CertificateSharingModule,
    CertificateReviewModule,
    CertificateRequestModule,
    
    // Analytics
    TutorAnalyticsModule,
    StudentAnalyticsModule,
    
    // Financial
    FinancialAidModule,
    AidApplicationModule,
    SubscriptionsModule,
    CartModule,
    
    // Content & Communication
    FAQModule,
    TermsConditionsModule,
    PrivacyPolicyModule,
    AboutSectionModule,
    ContactMessagesModule,
    NotificationsModule,
    
    // User Management
    OrganizationsModule,
    OrganizationMembersModule,
    WishlistModule,
    SavedCoursesModule,
    
    // Moderation & Support
    ReportAbuseModule,
    RemovalRequestsModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
