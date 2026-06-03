"""create reviews table

Revision ID: 20250602_reviews
Revises: add_tracking_fields_to_orders
Create Date: 2026-06-02 12:02:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "20250602_reviews"
down_revision: Union[str, None] = "8e4d2b3c5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reviews",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("order_id", UUID(as_uuid=True), nullable=False),
        sa.Column("restaurant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("delivery_partner_id", UUID(as_uuid=True), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["restaurant_id"], ["restaurants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["delivery_partner_id"], ["delivery_partners.id"], ondelete="SET NULL"),
    )
    op.create_index(op.f("ix_reviews_delivery_partner_id"), "reviews", ["delivery_partner_id"], unique=False)
    op.create_index(op.f("ix_reviews_order_id"), "reviews", ["order_id"], unique=False)
    op.create_index(op.f("ix_reviews_restaurant_id"), "reviews", ["restaurant_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reviews_restaurant_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_order_id"), table_name="reviews")
    op.drop_index(op.f("ix_reviews_delivery_partner_id"), table_name="reviews")
    op.drop_table("reviews")
