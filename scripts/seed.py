"""Seed the local development database with sample data.
Run from the `backend` folder:

    python scripts\seed.py

This script is idempotent-ish: it checks for existing emails before creating users.
"""
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models.user import User
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem
from app.core.security import get_password_hash
from app.core.roles import Role


RESTAURANTS = [
    {
        "name": "Burger Barn",
        "description": "Juicy burgers and crispy fries made to order",
        "cuisine": "American",
        "address": "123 Main Street, Downtown",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "rating": 4.5,
        "delivery_time": 25,
        "menu_items": [
            {"category": "Starters", "name": "Loaded Nachos", "description": "Tortilla chips with cheese, jalapeños, and salsa", "price": 6.99, "is_veg": True},
            {"category": "Burgers", "name": "Classic Cheeseburger", "description": "Beef patty with cheese, lettuce, tomato, and our special sauce", "price": 12.99, "is_veg": False},
            {"category": "Burgers", "name": "Veggie Burger", "description": "Plant-based patty with avocado and sprouts", "price": 11.99, "is_veg": True},
            {"category": "Sides", "name": "Crispy Fries", "description": "Golden fries with sea salt", "price": 3.99, "is_veg": True},
            {"category": "Drinks", "name": "Milkshake", "description": "Creamy vanilla milkshake", "price": 4.99, "is_veg": True},
            {"category": "Dessert", "name": "Chocolate Sundae", "description": "Vanilla ice cream with chocolate syrup", "price": 5.49, "is_veg": True},
        ],
    },
    {
        "name": "Sushi Zen",
        "description": "Authentic Japanese sushi and sashimi",
        "cuisine": "Japanese",
        "address": "456 Oak Avenue, Westside",
        "latitude": 12.98,
        "longitude": 77.6,
        "rating": 4.7,
        "delivery_time": 35,
        "menu_items": [
            {"category": "Starters", "name": "Miso Soup", "description": "Traditional Japanese miso broth", "price": 2.99, "is_veg": True},
            {"category": "Sushi", "name": "California Roll", "description": "Crab, avocado, and cucumber roll", "price": 7.99, "is_veg": False},
            {"category": "Sushi", "name": "Vegetable Tempura Roll", "description": "Tempura vegetables with soy sauce", "price": 6.99, "is_veg": True},
            {"category": "Sashimi", "name": "Salmon Sashimi", "description": "Fresh salmon served with wasabi", "price": 9.99, "is_veg": False},
            {"category": "Noodles", "name": "Chicken Teriyaki", "description": "Grilled chicken with teriyaki glaze", "price": 13.99, "is_veg": False},
            {"category": "Dessert", "name": "Mochi Ice Cream", "description": "Green tea mochi with ice cream", "price": 4.99, "is_veg": True},
        ],
    },
    {
        "name": "Taco Fiesta",
        "description": "Fresh Mexican street tacos and more",
        "cuisine": "Mexican",
        "address": "789 Pine Lane, Eastside",
        "latitude": 12.96,
        "longitude": 77.58,
        "rating": 4.3,
        "delivery_time": 20,
        "menu_items": [
            {"category": "Tacos", "name": "Al Pastor Tacos", "description": "Marinated pork with pineapple, 3 pcs", "price": 8.99, "is_veg": False},
            {"category": "Tacos", "name": "Veggie Tacos", "description": "Grilled vegetables with corn salsa, 3 pcs", "price": 7.99, "is_veg": True},
            {"category": "Starters", "name": "Guacamole & Chips", "description": "Fresh avocado dip with tortilla chips", "price": 5.99, "is_veg": True},
            {"category": "Mains", "name": "Chicken Burrito", "description": "Large flour tortilla with rice, beans, and chicken", "price": 10.99, "is_veg": False},
            {"category": "Drinks", "name": "Horchata", "description": "Traditional Mexican rice drink", "price": 2.99, "is_veg": True},
            {"category": "Dessert", "name": "Churros", "description": "Cinnamon sugar churros with chocolate dip", "price": 4.49, "is_veg": True},
        ],
    },
    {
        "name": "Curry Palace",
        "description": "Authentic Indian curries and naan breads",
        "cuisine": "Indian",
        "address": "321 Maple Drive, Northside",
        "latitude": 12.99,
        "longitude": 77.57,
        "rating": 4.6,
        "delivery_time": 30,
        "menu_items": [
            {"category": "Starters", "name": "Samosa", "description": "Crispy pastry with spiced potatoes", "price": 4.99, "is_veg": True},
            {"category": "Curries", "name": "Butter Chicken", "description": "Tender chicken in creamy tomato sauce", "price": 14.99, "is_veg": False},
            {"category": "Curries", "name": "Paneer Tikka Masala", "description": "Grilled paneer in aromatic sauce", "price": 13.99, "is_veg": True},
            {"category": "Breads", "name": "Garlic Naan", "description": "Fresh naan with garlic butter", "price": 3.49, "is_veg": True},
            {"category": "Rice", "name": "Vegetable Biryani", "description": "Fragrant basmati rice with vegetables", "price": 11.99, "is_veg": True},
            {"category": "Dessert", "name": "Gulab Jamun", "description": "Sweet milk dumplings in rose syrup", "price": 3.99, "is_veg": True},
        ],
    },
    {
        "name": "Green Garden Cafe",
        "description": "Healthy salads, smoothies, and plant-based meals",
        "cuisine": "Healthy",
        "address": "654 Cedar Blvd, Southside",
        "latitude": 12.965,
        "longitude": 77.59,
        "rating": 4.4,
        "delivery_time": 20,
        "menu_items": [
            {"category": "Salads", "name": "Quinoa Bowl", "description": "Quinoa with roasted vegetables and tahini", "price": 9.99, "is_veg": True},
            {"category": "Salads", "name": "Greek Yogurt Parfait", "description": "Yogurt with granola and fresh berries", "price": 6.99, "is_veg": True},
            {"category": "Smoothies", "name": "Berry Blast", "description": "Mixed berries with banana and almond milk", "price": 5.99, "is_veg": True},
            {"category": "Mains", "name": "Grilled Salmon Bowl", "description": "Salmon with brown rice and steamed veggies", "price": 15.99, "is_veg": False},
            {"category": "Drinks", "name": "Fresh Green Juice", "description": "Kale, cucumber, and apple juice", "price": 4.99, "is_veg": True},
            {"category": "Dessert", "name": "Acai Bowl", "description": "Acai with granola and fresh fruit", "price": 7.49, "is_veg": True},
        ],
    },
]


def main():
    print("Creating DB tables (if missing)")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # create owners and customers
    owner_emails = ["owner@seed.local", "owner2@seed.local", "owner3@seed.local", "owner4@seed.local", "owner5@seed.local"]
    customer_email = "customer@seed.local"
    
    owners = []
    for i, email in enumerate(owner_emails):
        owner = db.query(User).filter(User.email == email).first()
        if not owner:
            owner = User(
                name=f"Restaurant Owner {i+1}",
                email=email,
                phone=f"111{i}111111",
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
        owners.append(owner)

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

    # create restaurants with menu items
    total_items = 0
    for i, rest_data in enumerate(RESTAURANTS):
        restaurant = db.query(Restaurant).filter(Restaurant.name == rest_data["name"]).first()
        if not restaurant:
            restaurant = Restaurant(
                owner_id=owners[i % len(owners)].id,
                name=rest_data["name"],
                description=rest_data["description"],
                cuisine=rest_data["cuisine"],
                address=rest_data["address"],
                latitude=rest_data["latitude"],
                longitude=rest_data["longitude"],
                rating=rest_data["rating"],
                delivery_time=rest_data["delivery_time"],
                is_active=True,
            )
            db.add(restaurant)
            db.commit()
            db.refresh(restaurant)
            print(f"Created restaurant: {restaurant.name} (id={restaurant.id})")
        else:
            print(f"Restaurant already exists: {restaurant.name} (id={restaurant.id})")

        for mi_data in rest_data["menu_items"]:
            exists = db.query(MenuItem).filter(
                MenuItem.name == mi_data["name"],
                MenuItem.restaurant_id == restaurant.id
            ).first()
            if not exists:
                mi = MenuItem(
                    restaurant_id=restaurant.id,
                    category=mi_data["category"],
                    name=mi_data["name"],
                    description=mi_data["description"],
                    price=mi_data["price"],
                    image_url="",
                    is_veg=mi_data["is_veg"],
                    is_available=True,
                )
                db.add(mi)
                db.commit()
                db.refresh(mi)
                total_items += 1
                print(f"Added menu item: {mi.name} for {restaurant.name}")
            else:
                print(f"Menu item exists: {exists.name}")

    print(f"Seed complete — {total_items} new menu items added.")
    db.close()


if __name__ == "__main__":
    main()
