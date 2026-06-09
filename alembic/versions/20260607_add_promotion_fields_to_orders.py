"""add promotion fields to orders

Revision ID: 20260607_add_promotion_fields_to_orders
Revises: 20260607_add_promotions
Create Date: 2026-06-07 00:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260607_add_promotion_fields_to_orders'
down_revision = '20260607_add_promotions'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('orders', sa.Column('discount_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('applied_promotion_id', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    op.drop_column('orders', 'applied_promotion_id')
    op.drop_column('orders', 'discount_amount')
