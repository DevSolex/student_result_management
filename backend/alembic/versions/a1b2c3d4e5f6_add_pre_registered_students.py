"""add pre_registered_students table

Revision ID: a1b2c3d4e5f6
Revises: 18cd7b503cd5
Create Date: 2026-04-01 22:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '18cd7b503cd5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'pre_registered_students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matric_number', sa.String(length=50), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('matric_number'),
    )
    op.create_index(op.f('ix_pre_registered_students_id'), 'pre_registered_students', ['id'], unique=False)
    op.create_index(op.f('ix_pre_registered_students_matric_number'), 'pre_registered_students', ['matric_number'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_pre_registered_students_matric_number'), table_name='pre_registered_students')
    op.drop_index(op.f('ix_pre_registered_students_id'), table_name='pre_registered_students')
    op.drop_table('pre_registered_students')
