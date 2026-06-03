from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import Role
from app.crud.user import get_user, list_users
from app.crud.review import get_review as get_review_by_id, delete_review as delete_review_crud
from app.crud.coupon import create_coupon, get_coupon, get_coupons, update_coupon, delete_coupon as delete_coupon_crud
from app.db.models.coupon import Coupon
from app.schemas.coupon import CouponCreate, CouponUpdate, CouponRead
from app.core.monitoring import get_recent_errors, get_endpoint_counts
from app.crud.restaurant import get_restaurant
from app.db.models.user import User
from app.db.models.restaurant import Restaurant
from app.db.models.review import Review
from app.schemas.user import UserRead, UserUpdate
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter()


# Users
@router.get("/users", response_model=List[UserRead], summary="List users")
def list_users_route(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    return list_users(db, skip=skip, limit=limit)


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


@router.patch("/users/{user_id}", response_model=UserRead, summary="Block or unblock a user")
def update_user(
    user_id: str,
    payload: UserUpdate,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if str(user.id) == str(current_user.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot modify yourself.")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# Restaurants
@router.get("/restaurants", response_model=List[dict], summary="List all restaurants")
def list_restaurants(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurants = db.query(Restaurant).offset(skip).limit(limit).all()
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


@router.patch("/restaurants/{restaurant_id}", response_model=dict, summary="Approve, reject, or suspend a restaurant")
def update_restaurant(
    restaurant_id: str,
    payload: dict,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    action = payload.get("action")
    if action not in {"approve", "reject", "suspend"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action. Use approve, reject, or suspend.")

    if action == "approve":
        restaurant.is_active = True
    elif action == "reject":
        restaurant.is_active = False
    elif action == "suspend":
        restaurant.is_active = False

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return {
        "id": str(restaurant.id),
        "name": restaurant.name,
        "is_active": restaurant.is_active,
        "action": action,
    }


# Reviews
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


# Coupons
@router.post("", response_model=CouponRead, status_code=status.HTTP_201_CREATED, summary="Create a coupon")
def create_coupon_route(
    payload: CouponCreate,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    existing = get_coupon_by_code(db, payload.code)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Coupon code already exists.")
    return create_coupon(db, payload)


@router.get("", response_model=List[CouponRead], summary="List all coupons")
def list_coupons(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
    db: Session = Depends(get_db),
):
    return get_coupons(db, skip=skip, limit=limit)


@router.patch("/{coupon_id}", response_model=CouponRead, summary="Update a coupon")
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


@router.delete("/{coupon_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a coupon")
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
