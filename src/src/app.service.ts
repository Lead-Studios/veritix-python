import { Injectable } from '@nestjs/common';

@Injectable()
export class AppService {
  getHello(): object {
    return {
      message: 'Welcome to Hackathon Backend API',
      version: '1.0.0',
      description: 'NestJS backend with 40 issue modules',
    };
  }

  getAllModules(): object {
    return {
      modules: [
        'issue-01', 'issue-02', 'issue-03', 'issue-04', 'issue-05',
        'issue-06', 'issue-07', 'issue-08', 'issue-09', 'issue-10',
        'issue-11', 'issue-12', 'issue-13', 'issue-14', 'issue-15',
        'issue-16', 'issue-17', 'issue-18', 'issue-19', 'issue-20',
        'issue-21', 'issue-22', 'issue-23', 'issue-24', 'issue-25',
        'issue-26', 'issue-27', 'issue-28', 'issue-29', 'issue-30',
        'issue-31', 'issue-32', 'issue-33', 'issue-34', 'issue-35',
        'issue-36', 'issue-37', 'issue-38', 'issue-39', 'issue-40',
      ],
      total: 40,
    };
  }
}
