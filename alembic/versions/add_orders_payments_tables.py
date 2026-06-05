"""Add orders, order_items, and payments tables

Revision ID: 8e4d2b3c5f6a
Revises:
Create Date: 2026-06-02 12:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "8e4d2b3c5f6a"
down_revision: Union[str, None] = "7f3c1a2b4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "customer_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "restaurant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("restaurants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "address_id",
            UUID(as_uuid=True),
            sa.ForeignKey("addresses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("delivery_address_text", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Float(), nullable=False, default=0.0),
        sa.Column("delivery_fee", sa.Float(), nullable=False, default=0.0),
        sa.Column("gst", sa.Float(), nullable=False, default=0.0),
        sa.Column("total_amount", sa.Float(), nullable=False, default=0.0),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "order_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "order_id",
            UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "menu_item_id",
            UUID(as_uuid=True),
            sa.ForeignKey("menu_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price", sa.Float(), nullable=False, default=0.0),
        sa.Column("quantity", sa.Integer(), nullable=False, default=1),
    )

    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "order_id",
            UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("amount", sa.Float(), nullable=False, default=0.0),
        sa.Column("method", sa.String(50), nullable=False, default="cod"),
        sa.Column("status", sa.String(50), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
