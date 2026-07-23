"""Fix shift time columns to TIME type
Revision ID: a4b3ea7048f3
Revises: 8261edacdccd
Create Date: 2026-06-08 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'a4b3ea7048f3'
down_revision = '8261edacdccd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.alter_column('start_time',
               existing_type=sa.String(length=20),
               type_=sa.Time(),
               nullable=False)
        batch_op.alter_column('end_time',
               existing_type=sa.String(length=20),
               type_=sa.Time(),
               nullable=False)


def downgrade():
    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.alter_column('start_time',
               existing_type=sa.Time(),
               type_=sa.String(length=20),
               nullable=True)
        batch_op.alter_column('end_time',
               existing_type=sa.Time(),
               type_=sa.String(length=20),
               nullable=True)
