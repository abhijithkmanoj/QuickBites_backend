"""rename metadata columns to avoid SQLAlchemy reserved name

Revision ID: 20260608_rename_metadata
Revises: 
Create Date: 2026-06-08 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '20260608_rename_metadata'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # rename metadata -> metadata_json on promotions and payments
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='metadata') THEN
            EXECUTE 'ALTER TABLE promotions RENAME COLUMN metadata TO metadata_json';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='metadata') THEN
            EXECUTE 'ALTER TABLE payments RENAME COLUMN metadata TO metadata_json';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='driver_payouts' AND column_name='metadata') THEN
            EXECUTE 'ALTER TABLE driver_payouts RENAME COLUMN metadata TO metadata_raw';
        END IF;
    END$$;
    """)


def downgrade():
    # reverse rename if present
    op.execute("""
    DO $$
    BEGIN
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='promotions' AND column_name='metadata_json') THEN
            EXECUTE 'ALTER TABLE promotions RENAME COLUMN metadata_json TO metadata';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='payments' AND column_name='metadata_json') THEN
            EXECUTE 'ALTER TABLE payments RENAME COLUMN metadata_json TO metadata';
        END IF;
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='driver_payouts' AND column_name='metadata_raw') THEN
            EXECUTE 'ALTER TABLE driver_payouts RENAME COLUMN metadata_raw TO metadata';
        END IF;
    END$$;
    """)
