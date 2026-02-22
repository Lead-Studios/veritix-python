import { MigrationInterface, QueryRunner, Table, TableForeignKey } from 'typeorm';

export class CreateCoursesTable1000000000002 implements MigrationInterface {
  public async up(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.createTable(
      new Table({
        name: 'courses',
        columns: [
          {
            name: 'id',
            type: 'uuid',
            isPrimary: true,
            generationStrategy: 'uuid',
          },
          {
            name: 'title',
            type: 'varchar',
          },
          {
            name: 'description',
            type: 'text',
          },
          {
            name: 'category',
            type: 'varchar',
          },
          {
            name: 'level',
            type: 'enum',
            enum: ['beginner', 'intermediate', 'advanced'],
            default: "'beginner'",
          },
          {
            name: 'price',
            type: 'decimal',
            precision: 10,
            scale: 2,
          },
          {
            name: 'duration',
            type: 'int',
            comment: 'Duration in hours',
          },
          {
            name: 'tutorId',
            type: 'uuid',
          },
          {
            name: 'isPublished',
            type: 'boolean',
            default: false,
          },
          {
            name: 'createdAt',
            type: 'timestamp',
            default: 'CURRENT_TIMESTAMP',
          },
          {
            name: 'updatedAt',
            type: 'timestamp',
            default: 'CURRENT_TIMESTAMP',
          },
        ],
      }),
    );

    await queryRunner.createForeignKey(
      'courses',
      new TableForeignKey({
        columnNames: ['tutorId'],
        referencedColumnNames: ['id'],
        referencedTableName: 'users',
        onDelete: 'CASCADE',
      }),
    );
  }

  public async down(queryRunner: QueryRunner): Promise<void> {
    await queryRunner.dropTable('courses');
  }
}
