from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.api.deps import get_db, require_roles
from app.core.roles import Role
from app.crud.user import get_user, list_users
from app.crud.review import get_review as get_review_by_id, delete_review as delete_review_crud
from app.crud.coupon import create_coupon, get_coupon, get_coupons, update_coupon, delete_coupon as delete_coupon_crud
from app.crud.restaurant import get_restaurant, get_restaurants, get_restaurants_by_owner
from app.crud.restaurant_owner_profile import get_owner_profile, update_verification_status
from app.crud.delivery_partner import get_delivery_partner_by_user
from app.crud.order import update_order_status
from app.services import realtime as realtime_service
from app.db.models.coupon import Coupon
from app.schemas.restaurant_owner_profile import VerificationStatus
from app.db.models.delivery_partner import DeliveryPartner
from app.db.models.restaurant_owner_profile import RestaurantOwnerProfile
from app.db.models.user import User
from app.db.models.restaurant import Restaurant
from app.db.models.review import Review
from app.db.models.order import Order
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponRead
from app.core.monitoring import get_recent_errors, get_endpoint_counts
from app.schemas.user import UserRead, UserUpdate
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter()


# ─── Admin Dashboard ───────────────────────────────────────────────────────────

@router.get("/dashboard", summary="Get admin dashboard statistics")
def admin_dashboard(
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    total_users = db.query(User).count()
    users_by_role = {
        Role.customer.value: db.query(User).filter(User.role == Role.customer.value).count(),
        Role.restaurant_owner.value: db.query(User).filter(User.role == Role.restaurant_owner.value).count(),
        Role.delivery_partner.value: db.query(User).filter(User.role == Role.delivery_partner.value).count(),
        Role.admin.value: db.query(User).filter(User.role == Role.admin.value).count(),
    }

    total_restaurants = db.query(Restaurant).count()
    restaurants_by_status = {
        "active": db.query(Restaurant).filter(Restaurant.is_active == True).count(),
        "inactive": db.query(Restaurant).filter(Restaurant.is_active == False).count(),
    }

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    orders_today = db.query(Order).filter(Order.created_at >= today_start).count()
    revenue_today = db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(
        Order.status == "delivered",
        Order.created_at >= today_start
    ).scalar()
    active_deliveries = db.query(Order).filter(
        Order.status.in_(["picked_up", "out_for_delivery"])
    ).count()
    new_signups_today = db.query(User).filter(User.created_at >= today_start).count()

    return {
        "total_users": total_users,
        "users_by_role": users_by_role,
        "total_restaurants": total_restaurants,
        "restaurants_by_status": restaurants_by_status,
        "orders_today": orders_today,
        "revenue_today": float(revenue_today),
        "active_deliveries_now": active_deliveries,
        "new_signups_today": new_signups_today,
    }


# ─── User Management ─────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserRead], summary="List users with filters")
def list_users_route(
    skip: int = 0,
    limit: int = 50,
    role: str | None = Query(None, description="Filter by role"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    return query.offset(skip).limit(limit).all()


@router.get("/users/{user_id}", response_model=UserRead, summary="Get user details")
def get_user_details(
    user_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.patch("/users/{user_id}/block", response_model=UserRead, summary="Block a user")
def block_user(
    user_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot block yourself.")
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/unblock", response_model=UserRead, summary="Unblock a user")
def unblock_user(
    user_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ─── Restaurant Management ───────────────────────────────────────────────────

@router.get("/restaurants", summary="List restaurants with filters")
def list_restaurants(
    skip: int = 0,
    limit: int = 50,
    approval_status: str | None = Query(None, description="Filter by approval status"),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(Restaurant)
    if approval_status:
        if approval_status == "approved":
            query = query.filter(Restaurant.is_active == True)
        elif approval_status in ("pending", "suspended"):
            query = query.filter(Restaurant.is_active == False)
    restaurants = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "cuisine": r.cuisine,
            "address": r.address,
            "is_active": r.is_active,
            "rating": r.rating,
            "delivery_time": r.delivery_time,
            "owner_id": str(r.owner_id) if r.owner_id else None,
        }
        for r in restaurants
    ]


@router.get("/restaurants/{restaurant_id}", summary="Get restaurant detail for admin")
def get_restaurant_detail(
    restaurant_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "description": restaurant.description,
        "cuisine": restaurant.cuisine,
        "address": restaurant.address,
        "is_active": restaurant.is_active,
        "rating": restaurant.rating,
    }


@router.patch("/restaurants/{restaurant_id}/approve", summary="Approve a restaurant")
def approve_restaurant(
    restaurant_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    restaurant.is_active = True
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.patch("/restaurants/{restaurant_id}/reject", summary="Reject a restaurant")
def reject_restaurant(
    restaurant_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    restaurant.is_active = False
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


@router.get("/owners", summary="List restaurant owner profiles")
def list_owner_profiles(
    skip: int = 0,
    limit: int = 50,
    verification_status: str | None = Query(None, description="Filter by verification status"),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(RestaurantOwnerProfile)
    if verification_status:
        query = query.filter(RestaurantOwnerProfile.verification_status == verification_status)
    profiles = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(profile.id),
            "user_id": str(profile.user_id),
            "business_name": profile.business_name,
            "verification_status": profile.verification_status,
            "rejection_reason": profile.rejection_reason,
            "verified_at": profile.verified_at.isoformat() if profile.verified_at else None,
        }
        for profile in profiles
    ]


@router.patch("/owners/{owner_id}/approve", summary="Approve a restaurant owner")
def approve_restaurant_owner(
    owner_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    owner_profile = get_owner_profile(db, owner_id)
    if not owner_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner profile not found.")
    updated_profile = update_verification_status(db, owner_profile, VerificationStatus.approved)
    return {
        "id": str(updated_profile.id),
        "user_id": str(updated_profile.user_id),
        "verification_status": updated_profile.verification_status,
        "rejection_reason": updated_profile.rejection_reason,
        "verified_at": updated_profile.verified_at.isoformat() if updated_profile.verified_at else None,
    }


@router.patch("/owners/{owner_id}/reject", summary="Reject a restaurant owner")
def reject_restaurant_owner(
    owner_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    owner_profile = get_owner_profile(db, owner_id)
    if not owner_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner profile not found.")
    updated_profile = update_verification_status(db, owner_profile, VerificationStatus.rejected, reason)
    return {
        "id": str(updated_profile.id),
        "user_id": str(updated_profile.user_id),
        "verification_status": updated_profile.verification_status,
        "rejection_reason": updated_profile.rejection_reason,
        "verified_at": updated_profile.verified_at.isoformat() if updated_profile.verified_at else None,
    }


@router.patch("/restaurants/{restaurant_id}/suspend", summary="Suspend a restaurant")
def suspend_restaurant(
    restaurant_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    restaurant.is_active = False
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


# ─── Delivery Partner Management ─────────────────────────────────────────────

@router.get("/partners", summary="List delivery partners with filters")
def list_partners(
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = Query(None, description="Filter by verification status"),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(DeliveryPartner)
    if status_filter:
        query = query.filter(DeliveryPartner.verification_status == status_filter)
    partners = query.offset(skip).limit(limit).all()
    return [
        {
            "id": str(p.id),
            "user_id": str(p.user_id),
            "vehicle_type": p.vehicle_type,
            "license_number": p.license_number,
            "is_available": p.is_available,
            "rating": p.rating,
            "verification_status": p.verification_status,
        }
        for p in partners
    ]


@router.patch("/partners/{partner_id}/approve", summary="Approve a delivery partner")
def approve_partner(
    partner_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found.")
    partner.verification_status = "approved"
    partner.verified_at = datetime.utcnow()
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.patch("/partners/{partner_id}/reject", summary="Reject a delivery partner")
def reject_partner(
    partner_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found.")
    partner.verification_status = "rejected"
    partner.rejection_reason = reason
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


@router.patch("/partners/{partner_id}/suspend", summary="Suspend a delivery partner")
def suspend_partner(
    partner_id: str,
    reason: str | None = Body(default=None, embed=True),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    partner = db.query(DeliveryPartner).filter(DeliveryPartner.id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery partner not found.")
    partner.is_available = False
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


# ─── Order Management ─────────────────────────────────────────────────────────

@router.get("/orders", summary="List all orders (admin)")
def list_orders(
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = Query(None, description="Filter by status"),
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


# ─── Reviews ────────────────────────────────────────────────────────────────

@router.get("/reviews", response_model=List[ReviewRead], summary="List all reviews")
def list_reviews(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    return db.query(Review).order_by(Review.created_at.desc()).offset(skip).limit(limit).all()


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a fake review")
def delete_review(
    review_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        parsed_id = uuid.UUID(review_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid review id.")
    review = get_review_by_id(db, parsed_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found.")
    delete_review_crud(db, review)
    return None


# ─── Coupons ────────────────────────────────────────────────────────────────

@router.post("/coupons", response_model=CouponRead, status_code=status.HTTP_201_CREATED, summary="Create a coupon")
def create_coupon_route(
    payload: CouponCreate,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    existing = db.query(Coupon).filter(Coupon.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists.")
    return create_coupon(db, payload)


@router.get("/coupons", response_model=List[CouponRead], summary="List all coupons")
def list_coupons(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    return get_coupons(db, skip=skip, limit=limit)


@router.patch("/coupons/{coupon_id}", response_model=CouponRead, summary="Update a coupon")
def update_coupon_route(
    coupon_id: str,
    payload: CouponUpdate,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        parsed_id = uuid.UUID(coupon_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid coupon id.")
    coupon = get_coupon(db, parsed_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
    return update_coupon(db, coupon, payload)


@router.delete("/coupons/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a coupon")
def delete_coupon_route(
    coupon_id: str,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    import uuid
    try:
        parsed_id = uuid.UUID(coupon_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid coupon id.")
    coupon = get_coupon(db, parsed_id)
    if not coupon:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coupon not found.")
    delete_coupon_crud(db, coupon)
    return None


@router.get("/monitoring/errors", summary="Get recent error events")
def recent_errors(
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
):
    return get_recent_errors(limit=limit)


@router.get("/monitoring/endpoints", summary="Get endpoint usage counts")
def endpoint_stats(
    current_user: User = Depends(require_roles(Role.admin)),
):
    return get_endpoint_counts()