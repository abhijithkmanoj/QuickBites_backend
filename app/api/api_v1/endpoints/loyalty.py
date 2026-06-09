from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.services import loyalty as loyalty_service
from app.db.models.user import User

router = APIRouter()


class RedeemRequest(BaseModel):
    reward_id: str


@router.get('/me')
def my_points(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    points = loyalty_service.get_points(db, current_user.id)
    return {'user_id': str(current_user.id), 'points': points}


@router.get('/rewards')
def list_rewards(db: Session = Depends(get_db)):
    rewards = loyalty_service.list_rewards(db)
    return {'rewards': [{'id': str(r.id), 'code': r.code, 'description': r.description, 'points_cost': r.points_cost} for r in rewards]}


@router.post('/redeem')
def redeem(req: RedeemRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    try:
        redemption = loyalty_service.redeem_reward(db, current_user.id, UUID(req.reward_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {'redemption_id': str(redemption.id), 'status': redemption.status}
