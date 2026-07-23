"""Add roles table and migrate role strings
Revision ID: 8261edacdccd
Revises: 4fe92801cb36
Create Date: 2026-06-08 12:53:53.702549
"""
from alembic import op
import sqlalchemy as sa

revision = '8261edacdccd'
down_revision = '4fe92801cb36'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Create the roles table.
    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # 2. Seed the three roles.
    op.execute("INSERT INTO roles (id, name, description) VALUES (1, 'admin', 'Full system access')")
    op.execute("INSERT INTO roles (id, name, description) VALUES (2, 'manager', 'Manage schedules')")
    op.execute("INSERT INTO roles (id, name, description) VALUES (3, 'employee', 'View own shifts')")

    # 3. Routes — drop location_id. In SQLite batch mode, dropping the column
    #    removes its FK constraint automatically. No drop_constraint needed.
    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('description',
               existing_type=sa.TEXT(),
               type_=sa.String(length=200),
               existing_nullable=True)
        batch_op.drop_column('location_id')

    # 4. Shifts — update column types, drop unused columns.
    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.alter_column('start_time',
               existing_type=sa.TIME(),
               type_=sa.String(length=20),
               nullable=True)
        batch_op.alter_column('end_time',
               existing_type=sa.TIME(),
               type_=sa.String(length=20),
               nullable=True)
        batch_op.alter_column('notes',
               existing_type=sa.TEXT(),
               type_=sa.String(length=300),
               existing_nullable=True)
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')

    # 5. Users FIRST PASS — add role_id and active, update types, drop
    #    location_id. Keep the role string column so step 6 can read it.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('role_id', sa.Integer(), nullable=True))
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=150),
               type_=sa.String(length=120),
               existing_nullable=False)
        batch_op.alter_column('password_hash',
               existing_type=sa.VARCHAR(length=200),
               type_=sa.String(length=128),
               existing_nullable=False)
        batch_op.drop_column('location_id')

    # 6. DATA MIGRATION — copy role strings to role_id before dropping role.
    op.execute("UPDATE users SET role_id = 2 WHERE role = 'manager'")
    op.execute("UPDATE users SET role_id = 3 WHERE role = 'employee'")

    # 7. Users SECOND PASS — add FK to roles, drop the old role string column.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_users_role_id', 'roles', ['role_id'], ['id'])
        batch_op.drop_column('role')

    # 8. Drop locations last — all FKs pointing to it are now gone.
    op.drop_table('locations')


def downgrade():
    op.create_table('locations',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('name', sa.VARCHAR(length=100), nullable=False),
        sa.Column('address', sa.VARCHAR(length=200), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('role', sa.VARCHAR(length=20),
                                      nullable=False, server_default='employee'))
        batch_op.drop_constraint('fk_users_role_id', type_='foreignkey')
        batch_op.create_foreign_key(None, 'locations', ['location_id'], ['id'])
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=128),
               type_=sa.VARCHAR(length=200),
               existing_nullable=False)
        batch_op.alter_column('email',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=150),
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)
        batch_op.drop_column('role_id')
        batch_op.drop_column('active')

    with op.batch_alter_table('shifts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DATETIME(), nullable=True))
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.alter_column('notes',
               existing_type=sa.String(length=300),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('end_time',
               existing_type=sa.String(length=20),
               type_=sa.TIME(),
               nullable=False)
        batch_op.alter_column('start_time',
               existing_type=sa.String(length=20),
               type_=sa.TIME(),
               nullable=False)

    with op.batch_alter_table('routes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key(None, 'locations', ['location_id'], ['id'])
        batch_op.alter_column('description',
               existing_type=sa.String(length=200),
               type_=sa.TEXT(),
               existing_nullable=True)
        batch_op.alter_column('name',
               existing_type=sa.String(length=120),
               type_=sa.VARCHAR(length=100),
               existing_nullable=False)

    op.drop_table('roles')
