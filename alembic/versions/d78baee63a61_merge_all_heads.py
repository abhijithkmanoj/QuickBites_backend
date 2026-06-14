"""merge_all_heads

Revision ID: d78baee63a61
Revises: 20260606_add_notifications_table, 20260607_add_chat_messages, 20260607_add_loyalty, 20260611_add_stock_quantity, add_address_details_to_addresses, add_performance_indexes, b2c3d4e5f6a7, a1b2c3d4e5f8
Create Date: 2026-06-12 12:30:57.974293

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd78baee63a61'
down_revision = ('20260606_add_notifications_table', '20260607_add_chat_messages', '20260607_add_loyalty', '20260611_add_stock_quantity', 'add_address_details_to_addresses', 'add_performance_indexes', 'b2c3d4e5f6a7', 'a1b2c3d4e5f8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
