#!/usr/bin/env python3
"""Seed the database with test data for all tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uuid
from datetime import datetime, timedelta
from random import choice, randint

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem
from app.db.models.address import Address
from app.db.models.order import Order, OrderItem
from app.db.models.payment import Payment
from app.db.models.delivery_partner import DeliveryPartner
from app.db.models.review import Review
from app.core.security import get_password_hash


def seed_users(db: Session) -> list[User]:
    users = [
        User(id=uuid.uuid4(), name="Admin User", email="admin@example.com", password_hash=get_password_hash("Password123"), role="admin", is_active=True),
        User(id=uuid.uuid4(), name="Restaurant Owner", email="owner@example.com", password_hash=get_password_hash("Password123"), role="restaurant_owner", is_active=True),
        User(id=uuid.uuid4(), name="Delivery Partner", email="partner@example.com", password_hash=get_password_hash("Password123"), role="delivery_partner", is_active=True),
        User(id=uuid.uuid4(), name="Customer One", email="customer1@example.com", password_hash=get_password_hash("Password123"), role="customer", is_active=True),
        User(id=uuid.uuid4(), name="Customer Two", email="customer2@example.com", password_hash=get_password_hash("Password123"), role="customer", is_active=True),
    ]
    db.add_all(users)
    db.commit()
    return users


def seed_restaurants(db: Session, owner: User) -> list[Restaurant]:
    restaurants = [
        Restaurant(id=uuid.uuid4(), owner_id=owner.id, name="Spice Garden", cuisine="Indian", address="MG Road, Bangalore", latitude=12.9716, longitude=77.5946, rating=4.5, delivery_time=30, is_active=True),
        Restaurant(id=uuid.uuid4(), owner_id=owner.id, name="Sushi Central", cuisine="Japanese", address="Brigade Road, Bangalore", latitude=12.9717, longitude=77.6096, rating=4.3, delivery_time=35, is_active=True),
        Restaurant(id=uuid.uuid4(), owner_id=owner.id, name="Pizza Hub", cuisine="Italian", address="Koramangala, Bangalore", latitude=12.9352, longitude=77.6245, rating=4.1, delivery_time=25, is_active=True),
    ]
    db.add_all(restaurants)
    db.commit()
    return restaurants


def seed_menu_items(db: Session, restaurants: list[Restaurant]) -> list[MenuItem]:
    items = []
    for restaurant in restaurants:
        items.extend([
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, name=f"{restaurant.name} Special", description="Chef's special", price=199.0, category="Main Course", is_veg=True, is_available=True),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant.id, name=f"{restaurant.name} Combo", description="Combo meal", price=249.0, category="Combo", is_veg=False, is_available=True),
        ])
    db.add_all(items)
    db.commit()
    return items


def seed_addresses(db: Session, customers: list[User]) -> list[Address]:
    addresses = []
    for customer in customers:
        addresses.append(Address(id=uuid.uuid4(), user_id=customer.id, street="123 Main St", city="Bangalore", state="Karnataka", postal_code="560001", landmark="Near Park", phone="9876543210", is_default=True))
        addresses.append(Address(id=uuid.uuid4(), user_id=customer.id, street="456 Side St", city="Bangalore", state="Karnataka", postal_code="560002", landmark="", phone="9876543211", is_default=False))
    db.add_all(addresses)
    db.commit()
    return addresses


def seed_orders(db: Session, customers: list[User], restaurants: list[Restaurant], addresses: list[Address], menu_items: list[MenuItem], partners: list[DeliveryPartner]) -> list[Order]:
    orders = []
    statuses = ["pending", "accepted", "preparing", "assigned", "picked_up", "delivered"]
    for customer in customers:
        for _ in range(3):
            restaurant = choice(restaurants)
            address = choice([a for a in addresses if a.user_id == customer.id])
            status = choice(statuses)
            order = Order(
                id=uuid.uuid4(),
                customer_id=customer.id,
                restaurant_id=restaurant.id,
                address_id=address.id,
                delivery_address_text=f"{address.street}, {address.city}",
                subtotal=399.0,
                delivery_fee=40.0,
                gst=20.0,
                total_amount=459.0,
                status=status,
            )
            if status in ("assigned", "picked_up", "delivered") and partners:
                order.delivery_partner_id = choice(partners).id
            orders.append(order)
    db.add_all(orders)
    db.commit()
    return orders


def seed_payments(db: Session, orders: list[Order]) -> list[Payment]:
    payments = []
    for order in orders:
        payments.append(Payment(id=uuid.uuid4(), order_id=order.id, user_id=order.customer_id, amount=order.total_amount, method="cod", status="completed"))
    db.add_all(payments)
    db.commit()
    return payments


def seed_delivery_partners(db: Session, users: list[User]) -> list[DeliveryPartner]:
    partners = []
    for user in users:
        if user.role == "delivery_partner":
            partners.append(DeliveryPartner(id=uuid.uuid4(), user_id=user.id, vehicle_type="Bike", license_number=f"DL{randint(100000, 999999)}", rating=4.5, is_available=True))
    db.add_all(partners)
    db.commit()
    return partners


def seed_reviews(db: Session, orders: list[Order], restaurants: list[Restaurant], partners: list[DeliveryPartner]) -> list[Review]:
    reviews = []
    for order in orders[:5]:
        restaurant = choice(restaurants)
        partner = choice(partners) if partners else None
        reviews.append(Review(id=uuid.uuid4(), order_id=order.id, restaurant_id=restaurant.id, delivery_partner_id=partner.id if partner else None, rating=randint(3, 5), review_text="Great service!"))
    db.add_all(reviews)
    db.commit()
    return reviews


def main() -> None:
    db: Session = SessionLocal()
    try:
        for model in [Review, Payment, OrderItem, Order, Address, MenuItem, Restaurant, DeliveryPartner, RefreshToken, User]:
            db.query(model).delete(synchronize_session=False)
        db.commit()

        users = seed_users(db)
        owner = next(u for u in users if u.role == "restaurant_owner")
        restaurants = seed_restaurants(db, owner)
        menu_items = seed_menu_items(db, restaurants)
        customers = [u for u in users if u.role == "customer"]
        addresses = seed_addresses(db, customers)
        partners = seed_delivery_partners(db, users)
        orders = seed_orders(db, customers, restaurants, addresses, menu_items[:2], partners)
        payments = seed_payments(db, orders)
        reviews = seed_reviews(db, orders, restaurants, partners)
        print("Seed data inserted successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
