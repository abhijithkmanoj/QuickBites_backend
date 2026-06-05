"""Extend delivery_partners table with verification fields (Phase 16.1)

Revision ID: a1b2c3d4e5f8
Revises: add_restaurant_owner_profiles
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, None] = "a1b2c3d4e5f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column("delivery_partners", sa.Column("aadhar_number", sa.String(12), nullable=True))
    op.add_column("delivery_partners", sa.Column("license_image_url", sa.String(255), nullable=True))
    op.add_column("delivery_partners", sa.Column("profile_image_url", sa.String(255), nullable=True))
    op.add_column("delivery_partners", sa.Column("vehicle_number", sa.String(20), nullable=True))
    op.add_column("delivery_partners", sa.Column("current_latitude", sa.Float(), nullable=True))
    op.add_column("delivery_partners", sa.Column("current_longitude", sa.Float(), nullable=True))
    op.add_column("delivery_partners", sa.Column("verification_status", sa.String(20), nullable=False, server_default="pending"))
    op.add_column("delivery_partners", sa.Column("rejection_reason", sa.Text(), nullable=True))
    op.add_column("delivery_partners", sa.Column("total_deliveries", sa.Float(), nullable=False, server_default="0"))
    op.add_column("delivery_partners", sa.Column("earnings_today", sa.Float(), nullable=False, server_default="0"))
    op.add_column("delivery_partners", sa.Column("earnings_total", sa.Float(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("delivery_partners", "earnings_total")
    op.drop_column("delivery_partners", "earnings_today")
    op.drop_column("delivery_partners", "total_deliveries")
    op.drop_column("delivery_partners", "rejection_reason")
    op.drop_column("delivery_partners", "verification_status")
    op.drop_column("delivery_partners", "current_longitude")
    op.drop_column("delivery_partners", "current_latitude")
    op.drop_column("delivery_partners", "vehicle_number")
    op.drop_column("delivery_partners", "profile_image_url")
    op.drop_column("delivery_partners", "license_image_url")
    op.drop_column("delivery_partners", "aadhar_number")