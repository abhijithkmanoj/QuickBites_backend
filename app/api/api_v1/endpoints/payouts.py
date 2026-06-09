from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.db.models.order import Order
from app.db.models.driver_payout import DriverPayout
from app.db.models.user import User

router = APIRouter()


class TipCreate(BaseModel):
    amount: float


class PayoutMarkPaid(BaseModel):
    payout_id: str


@router.post('/orders/{order_id}/tip')
def add_tip(order_id: str, payload: TipCreate, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # allow customer to add tip to their own order before delivery
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Order not found')
    if str(order.customer_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized to tip this order')
    try:
        cents = int(round(payload.amount * 100))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid amount')
    order.tip_amount = (order.tip_amount or 0) + payload.amount
    order.tip_amount_cents = (order.tip_amount_cents or 0) + cents
    # update totals
    order.total_amount = float((order.total_amount or 0) + payload.amount)
    db.add(order)
    db.commit()
    db.refresh(order)
    return {'order_id': str(order.id), 'tip_amount': order.tip_amount}


@router.get('/drivers/{driver_id}/payouts')
def list_payouts(driver_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # driver can view their payouts; admin can view any
    user = current_user
    if getattr(user, 'role', None) != 'admin' and str(user.id) != driver_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized')
    payouts = db.query(DriverPayout).filter(DriverPayout.driver_id == driver_id).order_by(DriverPayout.created_at.desc()).all()
    return {'payouts': [{
        'id': str(p.id),
        'amount_cents': p.amount_cents,
        'currency': p.currency,
        'status': p.status,
        'created_at': p.created_at,
        'paid_at': p.paid_at,
    } for p in payouts]}


@router.post('/payouts/{payout_id}/pay')
def mark_payout_paid(payout_id: str, payload: PayoutMarkPaid, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    # admin-only: mark payout as paid
    if getattr(current_user, 'role', None) != 'admin':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin role required')
    payout = db.query(DriverPayout).filter(DriverPayout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Payout not found')
    payout.status = 'paid'
    payout.paid_at = datetime.utcnow()
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {'payout_id': str(payout.id), 'status': payout.status}
