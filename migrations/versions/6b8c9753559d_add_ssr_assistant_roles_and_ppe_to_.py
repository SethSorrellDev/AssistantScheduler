"""Add SSR assistant roles and PPE to routes
Revision ID: 6b8c9753559d
Revises: c3c04d2ad28b
Create Date: 2026-06-14 10:37:54.451180
"""
from alembic import op
import sqlalchemy as sa

revision = '6b8c9753559d'
down_revision = 'c3c04d2ad28b'
branch_labels = None
depends_on = None


def upgrade():
    # --- Data migration: rename employee → ssr, add assistant ---
    op.execute("UPDATE roles SET name='ssr' WHERE name='employee'")
    op.execute(
        "INSERT INTO roles (name) SELECT 'assistant' WHERE NOT EXISTS "
        "(SELECT 1 FROM roles WHERE name='assistant')"
    )

    # --- Create locations table ---
    op.create_table(
        'locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # --- roles: drop obsolete description column ---
    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.drop_column('description')

    # --- routes: add ppe_required and location_id ---
    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ppe_required', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('location_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_routes_location_id', 'locations', ['location_id'], ['id']
        )

    # --- shifts: add created_at, updated_at; enforce NOT NULL on status ---
    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.add_column(sa.Column(
            'created_at', sa.DateTime(), nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ))
        batch_op.add_column(sa.Column(
            'updated_at', sa.DateTime(), nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP')
        ))
        batch_op.alter_column('status', nullable=False)

    # --- users: add new columns, clean up old ones ---
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('phone_number', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column(
            'notify_email', sa.Boolean(), nullable=False,
            server_default=sa.text('1')
        ))
        batch_op.add_column(sa.Column(
            'notify_sms', sa.Boolean(), nullable=False,
            server_default=sa.text('0')
        ))
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.create_unique_constraint('uq_users_email', ['email'])
        batch_op.create_foreign_key(
            'fk_users_location_id', 'locations', ['location_id'], ['id']
        )
        batch_op.drop_column('created_at')
        batch_op.drop_column('active')


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        batch_op.drop_constraint('fk_users_location_id', type_='foreignkey')
        batch_op.drop_constraint('uq_users_email', type_='unique')
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=1)
        batch_op.drop_column('notify_sms')
        batch_op.drop_column('notify_email')
        batch_op.drop_column('phone_number')
        batch_op.drop_column('location_id')

    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=True)
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')

    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_routes_location_id', type_='foreignkey')
        batch_op.drop_column('location_id')
        batch_op.drop_column('ppe_required')

    with op.batch_alter_table('roles', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('description', sa.VARCHAR(length=200), nullable=True)
        )

    op.drop_table('locations')

    # --- Reverse role data migration ---
    op.execute("DELETE FROM roles WHERE name='assistant'")
    op.execute("UPDATE roles SET name='employee' WHERE name='ssr'")
