"""Add controller metadata to access logs

Revision ID: c1d2e3f4a5b6
Revises: b7e1c9f2a1d4
Create Date: 2026-05-06 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1d2e3f4a5b6'
down_revision = 'b7e1c9f2a1d4'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('controller_type', sa.String(length=20), nullable=True, server_default='unifi'))
        batch_op.add_column(sa.Column('controller_site', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('ap_mac', sa.String(length=17), nullable=True))
        batch_op.add_column(sa.Column('gateway_mac', sa.String(length=17), nullable=True))
        batch_op.add_column(sa.Column('vlan_id', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('ssid', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.drop_column('ssid')
        batch_op.drop_column('vlan_id')
        batch_op.drop_column('gateway_mac')
        batch_op.drop_column('ap_mac')
        batch_op.drop_column('controller_site')
        batch_op.drop_column('controller_type')
