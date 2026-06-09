from sqlalchemy.orm import Session
from app.db.models.loyalty import LoyaltyAccount, Reward, RewardRedemption
from app.db.models.user import User
from uuid import UUID


def get_or_create_account(db: Session, user_id: UUID) -> LoyaltyAccount:
    acc = db.query(LoyaltyAccount).filter(LoyaltyAccount.user_id == user_id).first()
    if not acc:
        acc = LoyaltyAccount(user_id=user_id, points=0)
        db.add(acc)
        db.commit()
        db.refresh(acc)
    return acc


def get_points(db: Session, user_id: UUID) -> int:
    acc = get_or_create_account(db, user_id)
    return acc.points


def award_points_for_order(db: Session, order) -> int:
    # Simple rule: 1 point per 10 INR spent (rounded down)
    amount = getattr(order, 'total_amount', 0) or 0
    points = int(amount // 10)
    if points <= 0:
        return 0
    acc = get_or_create_account(db, order.customer_id)
    acc.points = (acc.points or 0) + points
    db.add(acc)
    # store awarded points on order if model supports it
    try:
        order.points_awarded = points
        db.add(order)
    except Exception:
        pass
    db.commit()
    return points


def list_rewards(db: Session):
    return db.query(Reward).filter(Reward.active == True).all()


def redeem_reward(db: Session, user_id: UUID, reward_id: UUID):
    acc = get_or_create_account(db, user_id)
    reward = db.query(Reward).filter(Reward.id == reward_id, Reward.active == True).first()
    if not reward:
        raise ValueError("Reward not found or inactive")
    if acc.points < reward.points_cost:
        raise ValueError("Insufficient points")
    acc.points -= reward.points_cost
    redemption = RewardRedemption(user_id=user_id, reward_id=reward_id, points_spent=reward.points_cost, status='completed')
    db.add(acc)
    db.add(redemption)
    db.commit()
    db.refresh(redemption)
    return redemption
