from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.roles import Role
from app.crud.menu_item import (
    create_menu_item,
    delete_menu_item,
    get_menu_item,
    get_menu_items_by_restaurant,
    update_menu_item,
)
from app.crud.restaurant import get_restaurant
from app.db.models.user import User
from app.schemas.menu_item import MenuItemCreate, MenuItemRead, MenuItemUpdate

router = APIRouter()


@router.post("", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED, summary="Create a menu item")
def create_menu_item_endpoint(
    menu_item_in: MenuItemCreate,
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    restaurant = get_restaurant(db, menu_item_in.restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    if current_user.role == Role.restaurant_owner.value and restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to add menu items for this restaurant.")

    return create_menu_item(db, menu_item_in)


@router.put("/{menu_item_id}", response_model=MenuItemRead, summary="Update a menu item")
def update_menu_item_endpoint(
    menu_item_id: str,
    menu_item_in: MenuItemUpdate,
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    menu_item = get_menu_item(db, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    if current_user.role == Role.restaurant_owner.value and menu_item.restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to modify this menu item.")

    return update_menu_item(db, menu_item, menu_item_in)


@router.delete("/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a menu item")
def delete_menu_item_endpoint(
    menu_item_id: str,
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    menu_item = get_menu_item(db, menu_item_id)
    if not menu_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found.")

    if current_user.role == Role.restaurant_owner.value and menu_item.restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions to delete this menu item.")

    delete_menu_item(db, menu_item)
    return None
