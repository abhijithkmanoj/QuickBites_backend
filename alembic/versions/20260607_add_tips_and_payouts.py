"""Add tipping fields to orders and driver_payouts table

Revision ID: 20260607_add_tips_and_payouts
Revises: 20260607_add_stripe_payments
Create Date: 2026-06-07 00:10:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260607_add_tips_and_payouts"
down_revision = "20260607_add_stripe_payments"
branch_labels = None
depends_on = None


def upgrade():
    # add tip fields to orders
    op.add_column('orders', sa.Column('tip_amount', sa.Float(), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('tip_amount_cents', sa.BigInteger(), nullable=True))

    # create driver_payouts table
    op.create_table(
        'driver_payouts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='inr'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('metadata', sa.String(length=1024), nullable=True),
    )


def downgrade():
    op.drop_table('driver_payouts')
    op.drop_column('orders', 'tip_amount_cents')
    op.drop_column('orders', 'tip_amount')
