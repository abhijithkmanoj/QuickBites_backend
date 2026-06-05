"""Add extended profile fields to users table (Phase 15.1)

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add extended profile columns — all nullable so existing rows are unaffected
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("date_of_birth", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("language_preference", sa.String(10), nullable=True, server_default="en"))
    op.add_column("users", sa.Column("notification_preference", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("privacy_settings", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("theme_preference", sa.String(20), nullable=True, server_default="system"))
    op.add_column("users", sa.Column("last_active_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("profile_image_url", sa.String(255), nullable=True))


def downgrade():
    op.drop_column("users", "profile_image_url")
    op.drop_column("users", "last_active_at")
    op.drop_column("users", "theme_preference")
    op.drop_column("users", "privacy_settings")
    op.drop_column("users", "notification_preference")
    op.drop_column("users", "language_preference")
    op.drop_column("users", "gender")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "bio")
