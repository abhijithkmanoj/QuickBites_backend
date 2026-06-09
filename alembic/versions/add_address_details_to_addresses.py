"""add address_line2 and unit to addresses

Revision ID: add_address_details_to_addresses
Revises: add_geocoding_fields_to_addresses
Create Date: 2026-06-08 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "add_address_details_to_addresses"
down_revision: Union[str, None] = "add_geocoding_fields_to_addresses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("addresses", sa.Column("address_line2", sa.String(255), nullable=True))
    op.add_column("addresses", sa.Column("unit", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("addresses", "unit")
    op.drop_column("addresses", "address_line2")
