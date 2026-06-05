import sys
from pathlib import Path

from sqlalchemy import inspect, text

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.models import MenuItem, Restaurant, User
from app.db.session import SessionLocal, engine

delete_order = [
    "user_favorites",
    "user_activity",
    "reviews",
    "payments",
    "cart_items",
    "orders",
    "carts",
    "restaurant_owner_profiles",
    "device_tokens",
    "refresh_tokens",
    "addresses",
    "coupons",
    "menu_items",
    "restaurants",
    "delivery_partners",
    "users",
]

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured before running reset_and_seed.py")

print("Resetting data in:", settings.database_url_info)

with engine.begin() as connection:
    inspector = inspect(connection)
    existing_tables = {name for name in inspector.get_table_names()}

    for table_name in delete_order:
        if table_name in existing_tables:
            connection.execute(text(f'DELETE FROM "{table_name}"'))
            print(f'Deleted rows from {table_name}')
        else:
            print(f'Skipped missing table {table_name}')

print("All existing app data cleared.")

with SessionLocal() as session:
    test_customer = User(
        name="QuickBites Tester",
        email="tester@quickbites.local",
        phone="5550001111",
        password_hash=get_password_hash("Test1234!"),
        role="customer",
        is_active=True,
    )
    test_owner = User(
        name="QuickBites Owner",
        email="owner@quickbites.local",
        phone="5550002222",
        password_hash=get_password_hash("Owner1234!"),
        role="restaurant_owner",
        is_active=True,
    )

    restaurant = Restaurant(
        owner=test_owner,
        name="QuickBites Test Kitchen",
        description="A fresh test restaurant for QuickBites.",
        cuisine="Indian",
        address="123 Test Street, Test City",
        latitude=37.7749,
        longitude=-122.4194,
        rating=4.8,
        delivery_time=30,
        is_active=True,
    )

    menu_item1 = MenuItem(
        restaurant=restaurant,
        category="Main",
        name="Test Paneer Masala",
        description="Creamy paneer in spiced tomato gravy.",
        price=12.99,
        is_veg=True,
        is_available=True,
    )
    menu_item2 = MenuItem(
        restaurant=restaurant,
        category="Sides",
        name="Test Garlic Naan",
        description="Soft naan brushed with garlic butter.",
        price=3.99,
        is_veg=True,
        is_available=True,
    )

    session.add_all([test_customer, test_owner, restaurant, menu_item1, menu_item2])
    session.commit()

print("Test data created.")
print("Login credentials:")
print("  Customer: tester@quickbites.local / Test1234!")
print("  Restaurant owner: owner@quickbites.local / Owner1234!")
