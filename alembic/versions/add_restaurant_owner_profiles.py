"""Create restaurant_owner_profiles table for owner verification

Revision ID: a1b2c3d4e5f7
Revises: add_user_profile_fields
Create Date: 2025-01-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        "restaurant_owner_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("business_name", sa.String(255), nullable=False),
        sa.Column("gstin", sa.String(15), nullable=True),
        sa.Column("fssai_license_number", sa.String(14), nullable=True),
        sa.Column("bank_account_number", sa.String(50), nullable=True),
        sa.Column("ifsc_code", sa.String(11), nullable=True),
        sa.Column("verification_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("verified_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_restaurant_owner_profiles_user_id", "restaurant_owner_profiles", ["user_id"])


def downgrade():
    op.drop_table("restaurant_owner_profiles")