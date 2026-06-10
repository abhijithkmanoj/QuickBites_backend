"""add ai_chat_messages table for per-user AI chat persistence

Revision ID: 20260610_add_ai_chat_messages
Revises: 20260608_rename_metadata
Create Date: 2026-06-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260610_add_ai_chat_messages'
down_revision = '20260608_rename_metadata'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_chat_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )


def downgrade():
    op.drop_table('ai_chat_messages')
