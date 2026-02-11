"""Phase V: Advanced Cloud Deployment schema

Revision ID: 20250210_phase_v_schema
Revises: 20250206_add_conversations
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250210_phase_v_schema'
down_revision = '20250206_add_conversations'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums first
    priority_enum = postgresql.ENUM('LOW', 'MEDIUM', 'HIGH', name='priorityenum')
    priority_enum.create(op.get_bind())

    frequency_enum = postgresql.ENUM('DAILY', 'WEEKLY', 'MONTHLY', name='frequencyenum')
    frequency_enum.create(op.get_bind())

    event_type_enum = postgresql.ENUM('created', 'updated', 'completed', 'deleted', name='eventtypeenum')
    event_type_enum.create(op.get_bind())

    # Extend tasks table with Phase V columns
    op.add_column('tasks', sa.Column('due_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('tasks', sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', name='priorityenum', create_type=False), nullable=False, server_default='MEDIUM'))
    op.add_column('tasks', sa.Column('tags', postgresql.JSON, nullable=False, server_default='[]'))
    op.add_column('tasks', sa.Column('recurring_task_id', sa.UUID(), nullable=True))

    # Create indexes for tasks
    op.create_index('idx_tasks_due_date', 'tasks', ['due_date'])
    op.create_index('idx_tasks_priority', 'tasks', ['priority'])
    op.create_index('idx_tasks_user_due_priority', 'tasks', ['user_id', 'due_date', 'priority'])

    # Foreign key to recurring_tasks (will be added after table creation)
    # op.create_foreign_key('fk_tasks_recurring_task', 'tasks', 'recurring_tasks', ['recurring_task_id'], ['id'])

    # Create recurring_tasks table
    op.create_table(
        'recurring_tasks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', name='frequencyenum', create_type=False), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_occurrence', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_recurring_tasks_user_id', 'recurring_tasks', ['user_id'])
    op.create_index('idx_recurring_tasks_next_occurrence', 'recurring_tasks', ['next_occurrence'])

    # Now add the foreign key from tasks to recurring_tasks
    op.create_foreign_key('fk_tasks_recurring_task', 'tasks', 'recurring_tasks', ['recurring_task_id'], ['id'])

    # Create task_events table (audit trail)
    op.create_table(
        'task_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_type', sa.Enum('created', 'updated', 'completed', 'deleted', name='eventtypeenum', create_type=False), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('event_data', postgresql.JSON(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_task_events_task_id', 'task_events', ['task_id'])
    op.create_index('idx_task_events_user_id', 'task_events', ['user_id'])
    op.create_index('idx_task_events_timestamp', 'task_events', ['timestamp'])
    op.create_index('idx_task_events_type', 'task_events', ['event_type'])

    # Create reminders table
    op.create_table(
        'reminders',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_id', sa.UUID(), nullable=False),
        sa.Column('remind_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reminders_task_id', 'reminders', ['task_id'])
    op.create_index('idx_reminders_remind_at', 'reminders', ['remind_at'])
    op.create_index('idx_reminders_sent', 'reminders', ['sent'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('reminders')
    op.drop_table('task_events')

    # Drop foreign key first
    op.drop_constraint('fk_tasks_recurring_task', 'tasks', type_='foreignkey')

    # Drop recurring_tasks table
    op.drop_index('idx_recurring_tasks_next_occurrence', 'recurring_tasks')
    op.drop_index('idx_recurring_tasks_user_id', 'recurring_tasks')
    op.drop_table('recurring_tasks')

    # Remove columns from tasks
    op.drop_index('idx_tasks_user_due_priority', 'tasks')
    op.drop_index('idx_tasks_priority', 'tasks')
    op.drop_index('idx_tasks_due_date', 'tasks')
    op.drop_column('tasks', 'recurring_task_id')
    op.drop_column('tasks', 'tags')
    op.drop_column('tasks', 'priority')
    op.drop_column('tasks', 'due_date')

    # Drop enums
    sa.Enum(name='eventtypeenum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='frequencyenum').drop(op.get_bind(), checkfirst=False)
    sa.Enum(name='priorityenum').drop(op.get_bind(), checkfirst=False)
