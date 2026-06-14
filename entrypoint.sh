#!/bin/sh
# =============================================================================
# QuickBites — Docker entrypoint
# =============================================================================
# Creates all database tables from the SQLAlchemy models, seeds the database
# with test users if none exist, then starts the FastAPI server.
#
# NOTE: Alembic migrations are intentionally skipped here because the
# project's migration chain is fundamentally broken — several base tables
# (users, delivery_partners, etc.) are referenced by migration scripts but
# were never created via migration. The canonical table definitions live
# in the SQLAlchemy models under app/db/models/.
# =============================================================================

set -e

echo "==> Creating database tables from models..."
python << 'PYEOF'
import sys
sys.path.insert(0, '/app')

from app.db.base import Base
from app.db.models.user import User
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem
from app.db.models.delivery_partner import DeliveryPartner
from app.core.config import settings
from app.core.security import get_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid

url = settings.DATABASE_URL
if url and url.startswith('postgresql://'):
    url = url.replace('postgresql://', 'postgresql+psycopg://', 1)

engine = create_engine(url)

# Import all models so they register with Base.metadata
import app.db.models  # noqa: F401

Base.metadata.create_all(bind=engine)
print('All tables created successfully.')

# ---------------------------------------------------------------------------
# Seed test users if none exist
# ---------------------------------------------------------------------------
Session = sessionmaker(bind=engine)
db = Session()

try:
    existing_count = db.query(User).count()
    if existing_count > 0:
        print(f'Skipping seed — {existing_count} user(s) already exist.')
    else:
        print('Seeding database with test users...')

        users = [
            User(id=uuid.uuid4(), name='Admin User', email='admin@example.com',
                 password_hash=get_password_hash('Password123'), role='admin', is_active=True),
            User(id=uuid.uuid4(), name='Restaurant Owner', email='owner@example.com',
                 password_hash=get_password_hash('Password123'), role='restaurant_owner', is_active=True),
            User(id=uuid.uuid4(), name='Delivery Partner', email='partner@example.com',
                 password_hash=get_password_hash('Password123'), role='delivery_partner', is_active=True),
            User(id=uuid.uuid4(), name='Customer One', email='customer1@example.com',
                 password_hash=get_password_hash('Password123'), role='customer', is_active=True),
            User(id=uuid.uuid4(), name='Customer Two', email='customer2@example.com',
                 password_hash=get_password_hash('Password123'), role='customer', is_active=True),
        ]
        db.add_all(users)
        db.flush()

        # Create a delivery partner record for the partner user
        partner_user = next(u for u in users if u.role == 'delivery_partner')
        db.add(DeliveryPartner(
            id=uuid.uuid4(), user_id=partner_user.id,
            vehicle_type='Bike', license_number='DL123456',
            rating=4.5, is_available=True,
        ))

        # Create a sample restaurant for the owner
        owner_user = next(u for u in users if u.role == 'restaurant_owner')
        restaurant = Restaurant(
            id=uuid.uuid4(), owner_id=owner_user.id,
            name='Spice Garden', cuisine='Indian',
            address='MG Road, Bangalore', latitude=12.9716, longitude=77.5946,
            rating=4.5, delivery_time=30, is_active=True,
        )
        db.add(restaurant)
        db.flush()

        # Add menu items for the restaurant
        db.add_all([
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id,
                     name='Butter Chicken', description='Creamy tomato curry with tender chicken',
                     price=299.0, category='Main Course', is_veg=False, is_available=True),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id,
                     name='Paneer Tikka', description='Grilled cottage cheese with spices',
                     price=249.0, category='Starters', is_veg=True, is_available=True),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id,
                     name='Garlic Naan', description='Oven-baked leavened bread with garlic',
                     price=59.0, category='Bread', is_veg=True, is_available=True),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id,
                     name='Biryani', description='Fragrant rice layered with spiced meat',
                     price=349.0, category='Main Course', is_veg=False, is_available=True),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id,
                     name='Mango Lassi', description='Chilled yogurt drink with mango',
                     price=99.0, category='Beverages', is_veg=True, is_available=True),
        ])

        db.commit()
        print('Seed complete — 5 test users created.')
        print('  Admin:           admin@example.com / Password123')
        print('  Owner:           owner@example.com / Password123')
        print('  Partner:         partner@example.com / Password123')
        print('  Customer 1:      customer1@example.com / Password123')
        print('  Customer 2:      customer2@example.com / Password123')
except Exception as e:
    db.rollback()
    print(f'Seed warning: {e}')
finally:
    db.close()

engine.dispose()
PYEOF

echo "==> Starting Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
