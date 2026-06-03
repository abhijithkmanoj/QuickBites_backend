from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.db.models.user import User
from app.services.recommendations import (
    get_personalized_recommendations,
    get_similar_food_recommendations,
    get_restaurant_recommendations,
)

router = APIRouter()


@router.get("", summary="Get recommendations")
def get_recommendations(
    user_id: str | None = Query(None),
    menu_item_id: str | None = Query(None),
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    target_user_id = user_id or str(current_user.id)

    if menu_item_id:
        recommendations = get_similar_food_recommendations(db, menu_item_id, limit=limit)
        return {"type": "similar_food", "data": recommendations}

    recommendations = get_restaurant_recommendations(db, user_id=target_user_id, limit=limit)
    return {"type": "restaurant", "data": recommendations}
