"""add promotions tables

Revision ID: 20260607_add_promotions
Revises: 
Create Date: 2026-06-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260607_add_promotions'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'promotions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False, unique=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('discount_amount', sa.BigInteger(), nullable=True),
        sa.Column('discount_percent', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('scheduled_start_at', sa.DateTime(), nullable=True),
        sa.Column('scheduled_end_at', sa.DateTime(), nullable=True),
        sa.Column('target_segment', sa.String(length=50), nullable=True),
        sa.Column('is_stackable', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('stack_priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    op.create_table(
        'promotion_usages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('promotion_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('discount_applied', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('promotion_usages')
    op.drop_table('promotions')
