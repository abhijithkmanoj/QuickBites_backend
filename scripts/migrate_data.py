from pathlib import Path
import re
import sys
from sqlalchemy import create_engine, MetaData, Table, insert, inspect, text
from sqlalchemy.exc import SQLAlchemyError

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'
if not ENV_PATH.exists():
    raise SystemExit('backend/.env not found')

text_content = ENV_PATH.read_text(encoding='utf-8')
source_match = re.search(r'^DATABASE_SOURCE_URL=(.+)$', text_content, flags=re.MULTILINE)
target_match = re.search(r'^DATABASE_URL=(.+)$', text_content, flags=re.MULTILINE)
if not source_match or not target_match:
    raise SystemExit('DATABASE_SOURCE_URL and DATABASE_URL must be set in backend/.env')

SOURCE_URL = source_match.group(1).strip()
TARGET_URL = target_match.group(1).strip()
print('Source DB:', SOURCE_URL)
print('Target DB:', TARGET_URL)

copy_order = [
    'users',
    'restaurants',
    'delivery_partners',
    'menu_items',
    'coupons',
    'addresses',
    'refresh_tokens',
    'device_tokens',
    'restaurant_owner_profiles',
    'carts',
    'orders',
    'cart_items',
    'payments',
    'reviews',
    'user_activity',
    'user_favorites',
]

source_engine = create_engine(SOURCE_URL, future=True)
target_engine = create_engine(TARGET_URL, future=True)

try:
    with source_engine.connect() as source_conn, target_engine.connect() as target_conn:
        source_inspector = inspect(source_conn)
        target_inspector = inspect(target_conn)
        source_tables = source_inspector.get_table_names()
        target_tables = target_inspector.get_table_names()

        missing_source = [t for t in copy_order if t not in source_tables]
        missing_target = [t for t in copy_order if t not in target_tables]
        if missing_source:
            raise RuntimeError(
                'Source database is missing tables: ' + ', '.join(missing_source)
                + '. Verify DATABASE_SOURCE_URL or source schema.'
            )
        if missing_target:
            raise RuntimeError(
                'Target database is missing tables: ' + ', '.join(missing_target)
                + '. Run schema migration first.'
            )

        print('Cleaning target tables...')
        for table_name in reversed(copy_order):
            target_conn.execute(text(f'DELETE FROM "{table_name}"'))
            print(f'  Deleted rows from {table_name}')

        for table_name in copy_order:
            source_meta = MetaData()
            target_meta = MetaData()
            source_table = Table(table_name, source_meta, autoload_with=source_engine)
            target_table = Table(table_name, target_meta, autoload_with=target_engine)

            common_columns = [c.name for c in target_table.columns if c.name in source_table.c]
            if not common_columns:
                raise RuntimeError(f'No matching columns found for table {table_name}')

            count = source_conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"')).scalar_one()
            print(f'Copying {count} rows into {table_name}...')
            if count == 0:
                continue

            rows = source_conn.execute(
                text(f'SELECT {", ".join([f"\"{col}\"" for col in common_columns])} FROM "{table_name}"')
            ).mappings().all()

            if rows:
                target_conn.execute(insert(target_table), [dict(row) for row in rows])
                print(f'  Inserted {len(rows)} rows into {table_name}')
            else:
                print(f'  No rows to insert for {table_name}')

    print('Data migration completed successfully.')
except SQLAlchemyError as error:
    print('Migration failed:', error)
    raise
