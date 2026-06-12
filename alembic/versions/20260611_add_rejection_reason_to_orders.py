"""Add rejection_reason column to orders table

Revision ID: 20260611_add_rejection_reason
Revises: 20260610_add_ai_chat_messages
Create Date: 2026-06-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260611_add_rejection_reason'
down_revision = '20260610_add_ai_chat_messages'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('orders', sa.Column('rejection_reason', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('orders', 'rejection_reason')
