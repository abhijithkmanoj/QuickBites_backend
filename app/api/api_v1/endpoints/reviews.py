from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_db, get_current_active_user
from app.crud.review import create_review, get_reviews_for_restaurant
from app.db.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter()


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED, summary="Submit a review")
def submit_review(
    review_in: ReviewCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return create_review(db, review_in)


@router.get("", response_model=List[ReviewRead], summary="Get reviews")
def get_reviews(
    restaurant_id: str,
    db: Session = Depends(get_db),
):
    try:
        import uuid
        parsed_id = uuid.UUID(restaurant_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid restaurant id.")
    return get_reviews_for_restaurant(db, parsed_id)
