"""Add portal sessions for cooldown control

Revision ID: d4e5f6a7b8c9
Revises: c1d2e3f4a5b6
Create Date: 2026-05-21 17:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'portal_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mac', sa.String(length=17), nullable=False),
        sa.Column('mac_hash', sa.String(length=64), nullable=False),
        sa.Column('controller_type', sa.String(length=20), nullable=False),
        sa.Column('controller_site', sa.String(length=100), nullable=True),
        sa.Column('ssid', sa.String(length=100), nullable=True),
        sa.Column('auth_minutes', sa.Integer(), nullable=False),
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False),
        sa.Column('authorized_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('cooldown_until', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_portal_sessions_authorized_at'), 'portal_sessions', ['authorized_at'], unique=False)
    op.create_index(op.f('ix_portal_sessions_cooldown_until'), 'portal_sessions', ['cooldown_until'], unique=False)
    op.create_index(op.f('ix_portal_sessions_expires_at'), 'portal_sessions', ['expires_at'], unique=False)
    op.create_index(op.f('ix_portal_sessions_mac_hash'), 'portal_sessions', ['mac_hash'], unique=False)
    op.create_index('idx_portal_sessions_lookup', 'portal_sessions', ['mac_hash', 'controller_type', 'controller_site'], unique=False)


def downgrade():
    op.drop_index('idx_portal_sessions_lookup', table_name='portal_sessions')
    op.drop_index(op.f('ix_portal_sessions_mac_hash'), table_name='portal_sessions')
    op.drop_index(op.f('ix_portal_sessions_expires_at'), table_name='portal_sessions')
    op.drop_index(op.f('ix_portal_sessions_cooldown_until'), table_name='portal_sessions')
    op.drop_index(op.f('ix_portal_sessions_authorized_at'), table_name='portal_sessions')
    op.drop_table('portal_sessions')