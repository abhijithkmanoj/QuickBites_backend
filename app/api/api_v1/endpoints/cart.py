from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.crud.cart import get_cart_by_user, create_cart, add_item_to_cart, update_cart_item, remove_cart_item, clear_cart
from app.schemas.cart import CartRead, CartAddItemRequest, CartItemUpdate, CartItemRead

router = APIRouter()


@router.get("", response_model=CartRead, summary="Get current user's cart")
def read_cart(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = get_cart_by_user(db, current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
    # compute applicable promotions for cart total
    try:
        total_cents = int(sum([int(i.price * 100) * i.quantity for i in cart.items]))
    except Exception:
        total_cents = 0
    from app.services import promotions as promotions_service
    promos = promotions_service.evaluate_promotions(db, current_user.id, total_cents, None)
    # attach a lightweight summary on the returned cart object
    cart.applicable_promotions = [{'code': a['code'], 'promo_id': a['promo_id'], 'discount_cents': a['discount_cents']} for a in promos.get('applied', [])]
    return cart


@router.post("/add", response_model=CartRead, status_code=status.HTTP_201_CREATED, summary="Add item to cart")
def add_item(request: CartAddItemRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = get_cart_by_user(db, current_user.id)
    if not cart:
        cart = create_cart(db, current_user.id, request.restaurant_id)
    elif str(cart.restaurant_id) != str(request.restaurant_id):
        # simple cross-restaurant validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart contains items from another restaurant. Clear cart first.")

    add_item_to_cart(db, cart, request.item)
    db.refresh(cart)
    return cart


@router.put("/item/{item_id}", response_model=CartItemRead, summary="Update cart item quantity")
def update_item(item_id: UUID = Path(...), payload: CartItemUpdate = None, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = get_cart_by_user(db, current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
    item = next((i for i in cart.items if str(i.id) == str(item_id)), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    updated = update_cart_item(db, item, payload.quantity)
    return updated


@router.delete("/item/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove item from cart")
def delete_item(item_id: UUID = Path(...), current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = get_cart_by_user(db, current_user.id)
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found.")
    item = next((i for i in cart.items if str(i.id) == str(item_id)), None)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")
    remove_cart_item(db, item)
    return None


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Clear cart")
def clear_user_cart(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    cart = get_cart_by_user(db, current_user.id)
    if not cart:
        return None
    clear_cart(db, cart)
    return None
