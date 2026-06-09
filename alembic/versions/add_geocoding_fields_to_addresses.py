"""add geocoding fields to addresses

Revision ID: add_geocoding_fields_to_addresses
Revises: 20250602_reviews
Create Date: 2026-06-06 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "add_geocoding_fields_to_addresses"
down_revision: Union[str, None] = "20250602_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("addresses", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("addresses", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("addresses", sa.Column("formatted_address", sa.String(500), nullable=True))
    op.add_column("addresses", sa.Column("place_id", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("addresses", "place_id")
    op.drop_column("addresses", "formatted_address")
    op.drop_column("addresses", "longitude")
    op.drop_column("addresses", "latitude")
