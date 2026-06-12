"""Add stock_quantity column to menu_items table

Revision ID: 20260611_add_stock_quantity
Revises: 20260611_add_auto_handle_orders
Create Date: 2026-06-11 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260611_add_stock_quantity'
down_revision = '20260611_add_auto_handle_orders'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('menu_items', sa.Column('stock_quantity', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('menu_items', 'stock_quantity')
