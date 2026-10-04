"""add identity sub to users

Revision ID: 25e648d4098e
Revises: edb60f9515fb
"""
from alembic import op
import sqlalchemy as sa

revision = '25e648d4098e'
down_revision = 'edb60f9515fb'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('identity_sub', sa.String(length=36), nullable=True))
        batch_op.create_index('ix_users_identity_sub', ['identity_sub'], unique=True)
        batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=True)


def downgrade():
    # Fails if any user has no password hash; restore hashes first.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_index('ix_users_identity_sub')
        batch_op.drop_column('identity_sub')
