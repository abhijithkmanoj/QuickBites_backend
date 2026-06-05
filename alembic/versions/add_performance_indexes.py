"""Add performance indexes for common query patterns."""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_performance_indexes"
down_revision: Union[str, None] = "8e4d2b3c5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index("ix_restaurants_is_active", "restaurants", ["is_active"], unique=False)
    op.create_index("ix_orders_created_at", "orders", ["created_at"], unique=False)
    op.create_index("ix_payments_status", "payments", ["status"], unique=False)
    op.create_index("ix_reviews_created_at", "reviews", ["created_at"], unique=False)
    op.create_index("ix_users_email_active", "users", ["email", "is_active"], unique=False)


def downgrade():
    op.drop_index("ix_users_email_active", table_name="users")
    op.drop_index("ix_reviews_created_at", table_name="reviews")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_orders_created_at", table_name="orders")
    op.drop_index("ix_restaurants_is_active", table_name="restaurants")
