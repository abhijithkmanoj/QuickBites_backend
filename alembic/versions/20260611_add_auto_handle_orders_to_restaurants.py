"""Add auto_handle_orders column to restaurants table

Revision ID: 20260611_add_auto_handle_orders
Revises: 20260611_add_rejection_reason
Create Date: 2026-06-11 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260611_add_auto_handle_orders'
down_revision = '20260611_add_rejection_reason'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('restaurants', sa.Column('auto_handle_orders', sa.Boolean(), nullable=False, server_default='true'))


def downgrade():
    op.drop_column('restaurants', 'auto_handle_orders')
