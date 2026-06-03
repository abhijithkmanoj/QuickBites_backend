from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.db.models.order import Order
from app.db.models.restaurant import Restaurant
from app.db.models.delivery_partner import DeliveryPartner
from app.db.models.payment import Payment


def _today_range() -> tuple[datetime, datetime]:
    start = datetime.utcnow().date()
    end = start + timedelta(days=1)
    return datetime.combine(start, datetime.min.time()), datetime.combine(end, datetime.min.time())


def get_dashboard(db: Session) -> dict:
    today_start, today_end = _today_range()
    total_users = db.scalar(select(func.count(User.id)))
    total_restaurants = db.scalar(select(func.count(Restaurant.id)))
    delivered_orders_subq = (
        select(func.count(Order.id))
        .where(Order.status == "delivered")
        .subquery()
    )
    total_orders = db.scalar(select(func.count(Order.id)))
    active_partners = db.scalar(
        select(func.count(DeliveryPartner.id)).where(DeliveryPartner.is_available.is_(True))
    )
    daily_orders = db.scalar(
        select(func.count(Order.id)).where(
            Order.created_at >= today_start,
            Order.created_at < today_end,
        )
    )
    daily_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.status == "completed",
            Payment.created_at >= today_start,
            Payment.created_at < today_end,
        )
    )
    total_revenue = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.status == "completed")
    )
    recent_orders = db.execute(
        select(Order.created_at, Order.status, Order.total_amount)
        .order_by(Order.created_at.desc())
        .limit(20)
    ).all()
    return {
        "total_users": total_users or 0,
        "total_restaurants": total_restaurants or 0,
        "total_orders": total_orders or 0,
        "active_partners": active_partners or 0,
        "daily_orders": daily_orders or 0,
        "daily_revenue": round(float(daily_revenue or 0), 2),
        "total_revenue": round(float(total_revenue or 0), 2),
        "recent_orders": [
            {
                "created_at": row[0].isoformat() if row[0] else None,
                "status": row[1],
                "total_amount": round(float(row[2] or 0), 2),
            }
            for row in recent_orders
        ],
    }
