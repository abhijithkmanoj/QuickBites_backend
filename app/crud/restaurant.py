import uuid
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.restaurant import Restaurant
from app.db.models.restaurant_owner_profile import RestaurantOwnerProfile
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID | str:
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def get_restaurant(db: Session, restaurant_id: str | uuid.UUID) -> Restaurant | None:
    return db.query(Restaurant).filter(Restaurant.id == _parse_uuid(restaurant_id)).first()


def get_restaurants(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    cuisine: str | None = None,
    active: bool = True,
) -> list[Restaurant]:
    query = db.query(Restaurant).filter(Restaurant.is_active == active)
    if active:
        query = query.outerjoin(
            RestaurantOwnerProfile,
            Restaurant.owner_id == RestaurantOwnerProfile.user_id,
        ).filter(
            or_(
                Restaurant.owner_id == None,
                RestaurantOwnerProfile.verification_status == 'approved',
            )
        )
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(search_pattern),
                Restaurant.description.ilike(search_pattern),
                Restaurant.cuisine.ilike(search_pattern),
                Restaurant.address.ilike(search_pattern),
            )
        )
    if cuisine:
        query = query.filter(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    return query.offset(skip).limit(limit).all()


def get_nearby_restaurants(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    skip: int = 0,
    limit: int = 100,
) -> list[Restaurant]:
    degree_radius = radius_km / 111.0
    query = (
        db.query(Restaurant)
        .filter(
            Restaurant.is_active == True,
            Restaurant.latitude != None,
            Restaurant.longitude != None,
            Restaurant.latitude.between(latitude - degree_radius, latitude + degree_radius),
            Restaurant.longitude.between(longitude - degree_radius, longitude + degree_radius),
        )
    )
    query = query.outerjoin(
        RestaurantOwnerProfile,
        Restaurant.owner_id == RestaurantOwnerProfile.user_id,
    ).filter(
        or_(
            Restaurant.owner_id == None,
            RestaurantOwnerProfile.verification_status == 'approved',
        )
    )
    return query.offset(skip).limit(limit).all()


def get_restaurants_by_owner(db: Session, owner_id: str | uuid.UUID) -> list[Restaurant]:
    return db.query(Restaurant).filter(Restaurant.owner_id == _parse_uuid(owner_id)).all()


def create_restaurant(db: Session, restaurant_in: RestaurantCreate) -> Restaurant:
    owner_id = restaurant_in.owner_id
    if isinstance(owner_id, str):
        owner_id = uuid.UUID(owner_id)
    restaurant = Restaurant(
        owner_id=owner_id,
        name=restaurant_in.name,
        description=restaurant_in.description,
        cuisine=restaurant_in.cuisine,
        address=restaurant_in.address,
        latitude=restaurant_in.latitude,
        longitude=restaurant_in.longitude,
        rating=restaurant_in.rating or 0.0,
        delivery_time=restaurant_in.delivery_time,
        is_active=restaurant_in.is_active,
        auto_handle_orders=restaurant_in.auto_handle_orders,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def update_restaurant(db: Session, restaurant: Restaurant, restaurant_in: RestaurantUpdate) -> Restaurant:
    for field, value in restaurant_in.dict(exclude_unset=True).items():
        setattr(restaurant, field, value)
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    return restaurant


def delete_restaurant(db: Session, restaurant: Restaurant) -> None:
    db.delete(restaurant)
    db.commit()
