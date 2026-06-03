import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.review import Review
from app.schemas.review import ReviewCreate


def create_review(db: Session, review_in: ReviewCreate) -> Review:
    review = Review(
        order_id=review_in.order_id,
        restaurant_id=review_in.restaurant_id,
        delivery_partner_id=review_in.delivery_partner_id,
        rating=review_in.rating,
        review_text=review_in.review_text,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews_for_restaurant(db: Session, restaurant_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[Review]:
    return (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_review(db: Session, review_id: uuid.UUID) -> Optional[Review]:
    return db.query(Review).filter(Review.id == review_id).first()


def delete_review(db: Session, review: Review) -> None:
    db.delete(review)
    db.commit()
