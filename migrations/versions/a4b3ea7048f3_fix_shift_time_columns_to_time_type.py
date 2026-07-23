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
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        # PostgreSQL requires explicit USING clause for type casting
        op.execute("""
            ALTER TABLE shifts
            ALTER COLUMN start_time TYPE TIME WITHOUT TIME ZONE
            USING start_time::time without time zone
        """)
        op.execute("""
            ALTER TABLE shifts
            ALTER COLUMN end_time TYPE TIME WITHOUT TIME ZONE
            USING end_time::time without time zone
        """)
        op.execute("ALTER TABLE shifts ALTER COLUMN start_time SET NOT NULL")
        op.execute("ALTER TABLE shifts ALTER COLUMN end_time SET NOT NULL")
    else:
        # SQLite uses batch mode
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
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("""
            ALTER TABLE shifts
            ALTER COLUMN start_time TYPE VARCHAR(20)
            USING start_time::text
        """)
        op.execute("""
            ALTER TABLE shifts
            ALTER COLUMN end_time TYPE VARCHAR(20)
            USING end_time::text
        """)
        op.execute("ALTER TABLE shifts ALTER COLUMN start_time DROP NOT NULL")
        op.execute("ALTER TABLE shifts ALTER COLUMN end_time DROP NOT NULL")
    else:
        with op.batch_alter_table('shifts', schema=None) as batch_op:
            batch_op.alter_column('start_time',
                   existing_type=sa.Time(),
                   type_=sa.String(length=20),
                   nullable=True)
            batch_op.alter_column('end_time',
                   existing_type=sa.Time(),
                   type_=sa.String(length=20),
                   nullable=True)
