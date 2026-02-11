"""Remove telefone and data_nascimento from access_logs

Revision ID: b7e1c9f2a1d4
Revises: 8b864ec1a2c3
Create Date: 2026-02-11 15:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b7e1c9f2a1d4'
down_revision = '8b864ec1a2c3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.drop_column('telefone')
        batch_op.drop_column('data_nascimento')


def downgrade():
    with op.batch_alter_table('access_logs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('telefone', sa.String(length=500), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('data_nascimento', sa.String(length=500), nullable=False, server_default=''))
