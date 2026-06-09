"""Add driver_locations table

Revision ID: 20260607_add_driver_locations
Revises: 20260607_add_tips_and_payouts
Create Date: 2026-06-07 00:20:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260607_add_driver_locations"
down_revision = "20260607_add_tips_and_payouts"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'driver_locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('driver_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table('driver_locations')
