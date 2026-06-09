"""Add loyalty accounts, rewards and redemptions

Revision ID: 20260607_add_loyalty
Revises: 20260607_add_driver_locations
Create Date: 2026-06-07 00:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260607_add_loyalty"
down_revision = "20260607_add_driver_locations"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'loyalty_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'rewards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(length=64), nullable=False, unique=True),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('points_cost', sa.Integer(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'reward_redemptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reward_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('rewards.id', ondelete='SET NULL'), nullable=False),
        sa.Column('points_spent', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
    )


def downgrade():
    op.drop_table('reward_redemptions')
    op.drop_table('rewards')
    op.drop_table('loyalty_accounts')
