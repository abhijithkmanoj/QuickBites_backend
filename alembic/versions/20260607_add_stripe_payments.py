"""Add Stripe payment fields and payment_methods table

Revision ID: 20260607_add_stripe_payments
Revises: 8e4d2b3c5f6a
Create Date: 2026-06-07 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260607_add_stripe_payments"
down_revision = "8e4d2b3c5f6a"
branch_labels = None
depends_on = None


def upgrade():
    # payments table additions
    op.add_column("payments", sa.Column("stripe_payment_intent_id", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("currency", sa.String(length=3), nullable=True))
    op.add_column("payments", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column("payments", sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("payments", sa.Column("amount_cents", sa.BigInteger(), nullable=True))

    # create payment_methods table
    op.create_table(
        "payment_methods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("stripe_payment_method_id", sa.String(length=255), nullable=False, unique=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=True),
        sa.Column("card_brand", sa.String(length=50), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("card_exp_month", sa.Integer(), nullable=True),
        sa.Column("card_exp_year", sa.Integer(), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("payment_methods")
    op.drop_column("payments", "amount_cents")
    op.drop_column("payments", "metadata")
    op.drop_column("payments", "stripe_customer_id")
    op.drop_column("payments", "currency")
    op.drop_column("payments", "stripe_payment_intent_id")
