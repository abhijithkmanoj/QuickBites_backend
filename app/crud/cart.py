import uuid
from sqlalchemy.orm import Session
from app.db.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from app.db.models.menu_item import MenuItem


def get_cart_by_user(db: Session, user_id: str | uuid.UUID) -> Cart | None:
    return db.query(Cart).filter(Cart.user_id == (uuid.UUID(user_id) if isinstance(user_id, str) else user_id)).first()


def create_cart(db: Session, user_id: str | uuid.UUID, restaurant_id: str | uuid.UUID) -> Cart:
    cart = Cart(user_id=(uuid.UUID(user_id) if isinstance(user_id, str) else user_id), restaurant_id=(uuid.UUID(restaurant_id) if isinstance(restaurant_id, str) else restaurant_id))
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def add_item_to_cart(db: Session, cart: Cart, item_in: CartItemCreate) -> CartItem:
    # attempt to link to menu item if provided
    menu_item = None
    if item_in.menu_item_id:
        menu_item = db.query(MenuItem).filter(MenuItem.id == item_in.menu_item_id).first()

    cart_item = CartItem(
        cart_id=cart.id,
        menu_item_id=(menu_item.id if menu_item else None),
        name=item_in.name,
        price=item_in.price,
        quantity=item_in.quantity,
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def update_cart_item(db: Session, cart_item: CartItem, quantity: int) -> CartItem:
    cart_item.quantity = quantity
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


def remove_cart_item(db: Session, cart_item: CartItem) -> None:
    db.delete(cart_item)
    db.commit()


def clear_cart(db: Session, cart: Cart) -> None:
    for item in list(cart.items):
        db.delete(item)
    db.commit()
