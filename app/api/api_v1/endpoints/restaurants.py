from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.roles import Role
from app.crud.menu_item import get_menu_items_by_restaurant
from app.crud.restaurant import (
    create_restaurant,
    get_nearby_restaurants,
    get_restaurant,
    get_restaurants,
    get_restaurants_by_owner,
    update_restaurant,
)
from app.db.models.order import Order
from app.db.models.restaurant import Restaurant
from app.db.models.user import User
from app.schemas.menu_item import MenuItemRead
from app.schemas.restaurant import (
    DashboardOrderRead,
    OrderCounts,
    RestaurantCreate,
    RestaurantDashboard,
    RestaurantRead,
    RestaurantUpdate,
)

router = APIRouter()


def _build_dashboard_data(orders: list[Order]) -> dict:
    """Build dashboard response data from a list of orders."""
    incoming = []
    active = []
    completed = []
    for order in orders:
        dto = DashboardOrderRead.model_validate(order, from_attributes=True)
        if order.status == "pending":
            incoming.append(dto)
        elif order.status in ("accepted", "preparing", "ready_for_pickup", "picked_up"):
            active.append(dto)
        else:
            completed.append(dto)
    return {
        "order_counts": OrderCounts(
            incoming=len(incoming),
            active=len(active),
            completed=len(completed),
            total=len(orders),
        ),
        "incoming_orders": incoming,
        "active_orders": active,
        "completed_orders": completed,
    }


@router.get("", response_model=List[RestaurantRead], summary="List restaurants")
def list_restaurants(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search term for name, description, cuisine, or address."),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine."),
    active: bool = Query(True, description="Only include active restaurants."),
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return."),
):
    return get_restaurants(db, skip=skip, limit=limit, search=search, cuisine=cuisine, active=active)


def read_restaurant(restaurant_id: str, db: Session = Depends(get_db)):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    return restaurant


@router.get("/search", response_model=List[RestaurantRead], summary="Search restaurants")
def search_restaurants(
    db: Session = Depends(get_db),
    q: Optional[str] = Query(None, description="Search query for restaurants."),
    cuisine: Optional[str] = Query(None, description="Cuisine filter."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return get_restaurants(db, skip=skip, limit=limit, search=q, cuisine=cuisine)


@router.get("/nearby", response_model=List[RestaurantRead], summary="Find nearby restaurants")
def nearby_restaurants(
    db: Session = Depends(get_db),
    latitude: float = Query(..., description="Latitude to search near."),
    longitude: float = Query(..., description="Longitude to search near."),
    radius_km: float = Query(5.0, ge=0.1, le=100.0, description="Search radius in kilometers."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return get_nearby_restaurants(db, latitude=latitude, longitude=longitude, radius_km=radius_km, skip=skip, limit=limit)


@router.get("/{restaurant_id}", response_model=RestaurantRead, summary="Get restaurant details")
def read_restaurant(restaurant_id: str, db: Session = Depends(get_db)):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    return restaurant


@router.get("/{restaurant_id}/menu", response_model=list[MenuItemRead], summary="List restaurant menu items")
def list_restaurant_menu(restaurant_id: str, db: Session = Depends(get_db)):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    return get_menu_items_by_restaurant(db, restaurant_id)


@router.post("", response_model=RestaurantRead, status_code=status.HTTP_201_CREATED, summary="Create a restaurant")
def create_restaurant_endpoint(
    restaurant_in: RestaurantCreate,
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    if current_user.role == Role.restaurant_owner.value:
        restaurant_in.owner_id = str(current_user.id)
    elif current_user.role == Role.admin.value and restaurant_in.owner_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin creation requires owner_id.",
        )

    restaurant = create_restaurant(db, restaurant_in)
    return restaurant


@router.get("/owner/dashboard", response_model=RestaurantDashboard, summary="Restaurant owner dashboard")
def owner_dashboard(
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    """Get dashboard overview for the restaurant owner. Requires verification for restaurant_owner role."""
    if current_user.role == Role.admin.value:
        # Admin sees all restaurants — let them pick; for now return first 5
        restaurants = db.query(Restaurant).limit(5).all()
    else:
        # Check if owner profile exists and is verified
        from app.crud.restaurant_owner_profile import get_owner_profile
        owner_profile = get_owner_profile(db, current_user.id)
        if not owner_profile or owner_profile.verification_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Restaurant owner account not verified. Complete onboarding at /restaurant-owner/onboard.",
            )
        restaurants = get_restaurants_by_owner(db, current_user.id)

    if not restaurants:
        return RestaurantDashboard(
            restaurants=[],
            order_counts=OrderCounts(),
        )

    restaurant_ids = [r.id for r in restaurants]

    # Fetch orders for all owned restaurants
    orders = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.restaurant_id.in_(restaurant_ids))
        .order_by(Order.created_at.desc())
        .limit(100)
        .all()
    )

    dashboard_data = _build_dashboard_data(orders)
    return RestaurantDashboard(
        restaurants=restaurants,
        **dashboard_data,
    )


@router.put("/{restaurant_id}", response_model=RestaurantRead, summary="Update a restaurant")
def update_restaurant_endpoint(
    restaurant_id: str,
    restaurant_in: RestaurantUpdate,
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    if current_user.role != Role.admin.value and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to modify this restaurant.")

    updated_restaurant = update_restaurant(db, restaurant, restaurant_in)
    return updated_restaurant
