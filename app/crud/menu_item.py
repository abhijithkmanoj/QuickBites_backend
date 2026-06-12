import uuid
from sqlalchemy.orm import Session

from app.db.models.menu_item import MenuItem
from app.schemas.menu_item import MenuItemCreate, MenuItemUpdate


def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID | str:
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def get_menu_item(db: Session, menu_item_id: str | uuid.UUID) -> MenuItem | None:
    return db.query(MenuItem).filter(MenuItem.id == _parse_uuid(menu_item_id)).first()


def get_menu_items_by_restaurant(db: Session, restaurant_id: str | uuid.UUID) -> list[MenuItem]:
    return db.query(MenuItem).filter(MenuItem.restaurant_id == _parse_uuid(restaurant_id)).all()


def create_menu_item(db: Session, menu_item_in: MenuItemCreate) -> MenuItem:
    menu_item = MenuItem(
        restaurant_id=_parse_uuid(menu_item_in.restaurant_id),
        category=menu_item_in.category,
        name=menu_item_in.name,
        description=menu_item_in.description,
        price=menu_item_in.price,
        image_url=menu_item_in.image_url,
        is_veg=menu_item_in.is_veg,
        is_available=menu_item_in.is_available,
        stock_quantity=menu_item_in.stock_quantity,
    )
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)
    return menu_item


def update_menu_item(db: Session, menu_item: MenuItem, menu_item_in: MenuItemUpdate) -> MenuItem:
    for field, value in menu_item_in.dict(exclude_unset=True).items():
        setattr(menu_item, field, value)
    db.add(menu_item)
    db.commit()
    db.refresh(menu_item)
    return menu_item


def delete_menu_item(db: Session, menu_item: MenuItem) -> None:
    db.delete(menu_item)
    db.commit()
