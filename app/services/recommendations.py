"""Recommendation engine for QuickBites.

Provides:
- Personalized recommendations
- Similar food recommendations
- Restaurant recommendations
"""

from __future__ import annotations

import random
import uuid
from collections import Counter
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.order import Order
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem
from app.db.models.review import Review


def _ensure_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def _get_user_order_restaurant_ids(db: Session, user_id: str) -> list[str]:
    parsed_id = _ensure_uuid(user_id)
    return [
        str(row[0])
        for row in db.query(Order.restaurant_id).filter(Order.customer_id == parsed_id).all()
        if row[0] is not None
    ]


def _get_user_cuisines(db: Session, user_id: str) -> list[str]:
    restaurant_ids = _get_user_order_restaurant_ids(db, user_id)
    if not restaurant_ids:
        return []
    return [
        str(row[0])
        for row in db.query(Restaurant.cuisine)
        .filter(Restaurant.id.in_(restaurant_ids))
        .all()
        if row[0] is not None
    ]


def get_personalized_recommendations(db: Session, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
    restaurant_ids = _get_user_order_restaurant_ids(db, user_id)
    if not restaurant_ids:
        return get_trending_restaurants(db, limit=limit)

    restaurants = db.query(Restaurant).filter(Restaurant.id.in_(restaurant_ids)).all()
    return [_serialize_restaurant(r) for r in restaurants[:limit]]


def get_similar_food_recommendations(db: Session, menu_item_id: str, limit: int = 10) -> list[dict[str, Any]]:
    menu_item = db.query(MenuItem).filter(MenuItem.id == menu_item_id).first()
    if not menu_item:
        return []

    similar = (
        db.query(MenuItem)
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id)
        .filter(
            MenuItem.id != menu_item.id,
            MenuItem.restaurant_id != menu_item.restaurant_id,
            (MenuItem.category == menu_item.category) | (Restaurant.cuisine == menu_item.restaurant.cuisine),
        )
        .limit(limit)
        .all()
    )
    return [_serialize_menu_item(item) for item in similar]


def get_restaurant_recommendations(db: Session, user_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    if user_id:
        cuisines = _get_user_cuisines(db, user_id)
        if cuisines:
            most_common_cuisine = Counter(cuisines).most_common(1)[0][0]
            restaurants = (
                db.query(Restaurant)
                .filter(Restaurant.is_active.is_(True), Restaurant.cuisine == most_common_cuisine)
                .order_by(Restaurant.rating.desc())
                .limit(limit)
                .all()
            )
            if restaurants:
                return [_serialize_restaurant(r) for r in restaurants]

    return get_trending_restaurants(db, limit=limit)


def get_trending_restaurants(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    restaurants = db.query(Restaurant).filter(Restaurant.is_active.is_(True)).order_by(Restaurant.rating.desc()).limit(limit).all()
    return [_serialize_restaurant(r) for r in restaurants]


def _serialize_restaurant(restaurant: Restaurant) -> dict[str, Any]:
    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "cuisine": restaurant.cuisine,
        "address": restaurant.address,
        "rating": restaurant.rating,
        "delivery_time": restaurant.delivery_time,
        "is_active": restaurant.is_active,
    }


def _serialize_menu_item(item: MenuItem) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "restaurant_id": str(item.restaurant_id),
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "is_veg": item.is_veg,
        "is_available": item.is_available,
        "restaurant_name": item.restaurant.name if item.restaurant else None,
    }
