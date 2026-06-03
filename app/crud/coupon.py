import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate


def create_coupon(db: Session, coupon_in: CouponCreate) -> Coupon:
    coupon = Coupon(
        code=coupon_in.code.upper(),
        discount_type=coupon_in.discount_type,
        discount_value=coupon_in.discount_value,
        usage_limit=coupon_in.usage_limit,
        expiry_date=coupon_in.expiry_date,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def get_coupon(db: Session, coupon_id: uuid.UUID) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.id == coupon_id).first()


def get_coupon_by_code(db: Session, code: str) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.code == code.upper()).first()


def get_coupons(db: Session, skip: int = 0, limit: int = 50) -> List[Coupon]:
    return db.query(Coupon).order_by(Coupon.created_at.desc()).offset(skip).limit(limit).all()


def update_coupon(db: Session, coupon: Coupon, coupon_in: CouponUpdate) -> Coupon:
    if coupon_in.code is not None:
        coupon.code = coupon_in.code.upper()
    if coupon_in.discount_type is not None:
        coupon.discount_type = coupon_in.discount_type
    if coupon_in.discount_value is not None:
        coupon.discount_value = coupon_in.discount_value
    if coupon_in.usage_limit is not None:
        coupon.usage_limit = coupon_in.usage_limit
    if coupon_in.expiry_date is not None:
        coupon.expiry_date = coupon_in.expiry_date
    if coupon_in.is_active is not None:
        coupon.is_active = coupon_in.is_active

    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()
