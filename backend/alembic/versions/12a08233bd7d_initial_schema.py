"""initial_schema

Revision ID: 12a08233bd7d
Revises: 
Create Date: 2026-05-07 23:49:30.928032

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12a08233bd7d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types first
    contract_type_enum = sa.Enum('full_time', 'part_time', name='contracttype')
    contract_type_enum.create(op.get_bind(), checkfirst=True)

    teacher_status_enum = sa.Enum('active', 'on_leave', 'terminated', 'onboarding', name='teacherstatus')
    teacher_status_enum.create(op.get_bind(), checkfirst=True)

    class_status_enum = sa.Enum('planned', 'approved', 'timetabled', 'open', 'completed', 'cancelled', name='classstatus')
    class_status_enum.create(op.get_bind(), checkfirst=True)

    hc_status_enum = sa.Enum('open', 'in_review', 'approved', 'filled', 'cancelled', name='headcountrequeststatus')
    hc_status_enum.create(op.get_bind(), checkfirst=True)

    # ── centres ───────────────────────────────────────────────────────
    op.create_table(
        'centres',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
    )
    op.create_index('ix_centres_id', 'centres', ['id'])

    # ── teachers ──────────────────────────────────────────────────────
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('contract_type', contract_type_enum, nullable=False),
        sa.Column('contracted_hours', sa.Float(), nullable=False, server_default='0'),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('salary', sa.Float(), nullable=True),
        sa.Column('primary_centre_id', sa.Integer(), nullable=False),
        sa.Column('status', teacher_status_enum, nullable=True, server_default='active'),
        sa.Column('qualifications', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['primary_centre_id'], ['centres.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_teachers_id', 'teachers', ['id'])

    # ── rooms ─────────────────────────────────────────────────────────
    op.create_table(
        'rooms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('centre_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('has_projector', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('has_whiteboard', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['centre_id'], ['centres.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('centre_id', 'name', name='uq_room_per_centre'),
    )
    op.create_index('ix_rooms_id', 'rooms', ['id'])

    # ── classes ───────────────────────────────────────────────────────
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('centre_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('level', sa.String(50), nullable=True),
        sa.Column('required_teacher_qualification', sa.String(100), nullable=True),
        sa.Column('preferred_day', sa.String(20), nullable=True),
        sa.Column('preferred_start_time', sa.Time(), nullable=True),
        sa.Column('preferred_end_time', sa.Time(), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('status', class_status_enum, nullable=True, server_default='planned'),
        sa.Column('max_students', sa.Integer(), nullable=True, server_default='1'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['centre_id'], ['centres.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_classes_id', 'classes', ['id'])

    # ── teacher_availability ──────────────────────────────────────────
    op.create_table(
        'teacher_availability',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.String(20), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('teacher_id', 'day_of_week', 'start_time',
                            name='uq_teacher_availability_slot'),
    )
    op.create_index('ix_teacher_availability_id', 'teacher_availability', ['id'])

    # ── leaves ────────────────────────────────────────────────────────
    op.create_table(
        'leaves',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(255), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_leaves_id', 'leaves', ['id'])

    # ── timetable_slots ───────────────────────────────────────────────
    op.create_table(
        'timetable_slots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('room_id', sa.Integer(), nullable=True),
        sa.Column('day_of_week', sa.String(20), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('is_draft', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_timetable_slots_id', 'timetable_slots', ['id'])

    # ── headcount_requests ────────────────────────────────────────────
    op.create_table(
        'headcount_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('centre_id', sa.Integer(), nullable=False),
        sa.Column('contract_type', contract_type_enum, nullable=False),
        sa.Column('hours_per_week', sa.Float(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('status', hc_status_enum, nullable=True, server_default='open'),
        sa.Column('requested_by', sa.String(100), nullable=True),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['centre_id'], ['centres.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_headcount_requests_id', 'headcount_requests', ['id'])

    # ── forecast_periods ──────────────────────────────────────────────
    op.create_table(
        'forecast_periods',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('centre_id', sa.Integer(), nullable=False),
        sa.Column('week_start', sa.Date(), nullable=False),
        sa.Column('week_end', sa.Date(), nullable=False),
        sa.Column('projected_demand_hours', sa.Float(), nullable=True),
        sa.Column('available_ft_hours', sa.Float(), nullable=True),
        sa.Column('available_pt_hours', sa.Float(), nullable=True),
        sa.Column('unassigned_ft_rate', sa.Float(), nullable=True),
        sa.Column('available_teacher_rate', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['centre_id'], ['centres.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_forecast_periods_id', 'forecast_periods', ['id'])


def downgrade() -> None:
    op.drop_table('forecast_periods')
    op.drop_table('headcount_requests')
    op.drop_table('timetable_slots')
    op.drop_table('leaves')
    op.drop_table('teacher_availability')
    op.drop_table('classes')
    op.drop_table('rooms')
    op.drop_table('teachers')
    op.drop_table('centres')

    sa.Enum(name='headcountrequeststatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='classstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='teacherstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='contracttype').drop(op.get_bind(), checkfirst=True)