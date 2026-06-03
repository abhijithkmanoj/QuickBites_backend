"""Seed the local development database with sample data.
Run from the `backend` folder:

    .venv\Scripts\python.exe scripts\seed.py

This script is idempotent-ish: it checks for existing emails before creating users.
"""

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models.user import User
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem
from app.core.security import get_password_hash
from app.core.roles import Role


def main():
    print("Creating DB tables (if missing)")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # create owner
    owner_email = "owner@seed.local"
    owner = db.query(User).filter(User.email == owner_email).first()
    if not owner:
        owner = User(
            name="Seed Owner",
            email=owner_email,
            phone="1112223333",
            password_hash=get_password_hash("OwnerPass123"),
            role=Role.restaurant_owner.value,
            is_active=True,
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        print(f"Created owner: {owner.email} (id={owner.id})")
    else:
        print(f"Owner already exists: {owner.email} (id={owner.id})")

    # create customer
    customer_email = "customer@seed.local"
    customer = db.query(User).filter(User.email == customer_email).first()
    if not customer:
        customer = User(
            name="Seed Customer",
            email=customer_email,
            phone="9998887777",
            password_hash=get_password_hash("CustomerPass123"),
            role=Role.customer.value,
            is_active=True,
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        print(f"Created customer: {customer.email} (id={customer.id})")
    else:
        print(f"Customer already exists: {customer.email} (id={customer.id})")

    # create restaurant
    restaurant_name = "Seed Diner"
    restaurant = db.query(Restaurant).filter(Restaurant.name == restaurant_name).first()
    if not restaurant:
        restaurant = Restaurant(
            owner_id=owner.id,
            name=restaurant_name,
            description="A seeded restaurant for local testing.",
            cuisine="Global",
            address="123 Seed St",
            latitude=12.9716,
            longitude=77.5946,
            rating=4.5,
            delivery_time=30,
            is_active=True,
        )
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        print(f"Created restaurant: {restaurant.name} (id={restaurant.id})")
    else:
        print(f"Restaurant already exists: {restaurant.name} (id={restaurant.id})")

    # add menu items
    items = [
        {
            "category": "Starters",
            "name": "Garlic Bread",
            "description": "Crispy garlic bread with herb butter.",
            "price": 4.5,
            "image_url": "",
            "is_veg": True,
            "is_available": True,
        },
        {
            "category": "Main Course",
            "name": "Margherita Pizza",
            "description": "Classic cheese pizza with fresh basil.",
            "price": 9.99,
            "image_url": "",
            "is_veg": True,
            "is_available": True,
        },
        {
            "category": "Dessert",
            "name": "Chocolate Brownie",
            "description": "Warm brownie with ice cream.",
            "price": 5.25,
            "image_url": "",
            "is_veg": True,
            "is_available": True,
        },
    ]

    created = 0
    for it in items:
        exists = db.query(MenuItem).filter(MenuItem.name == it["name"], MenuItem.restaurant_id == restaurant.id).first()
        if not exists:
            mi = MenuItem(
                restaurant_id=restaurant.id,
                category=it["category"],
                name=it["name"],
                description=it["description"],
                price=it["price"],
                image_url=it["image_url"],
                is_veg=it["is_veg"],
                is_available=it["is_available"],
            )
            db.add(mi)
            db.commit()
            db.refresh(mi)
            created += 1
            print(f"Added menu item: {mi.name} (id={mi.id})")
        else:
            print(f"Menu item exists: {exists.name} (id={exists.id})")

    print(f"Seed complete — {created} new menu items added.")
    db.close()


if __name__ == "__main__":
    main()
