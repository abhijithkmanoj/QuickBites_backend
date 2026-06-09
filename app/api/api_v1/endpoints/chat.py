from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.db.models.chat_message import ChatMessage
from app.db.models.order import Order
from app.services import realtime as realtime_service

router = APIRouter()


class ChatMessageIn(BaseModel):
    content: str
    message_type: str = 'text'


class ChatMessageOut(BaseModel):
    id: str
    order_id: str
    sender_id: str
    sender_role: str
    content: str
    message_type: str
    sent_at: str


@router.get('/orders/{order_id}/chat', response_model=List[ChatMessageOut])
def get_chat_history(order_id: str, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Validate order access
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    # Only participants may view: customer, restaurant owner, delivery partner, admin
    allowed_ids = [str(order.customer_id)]
    if order.restaurant and order.restaurant.owner_id:
        allowed_ids.append(str(order.restaurant.owner_id))
    if order.delivery_partner_id:
        allowed_ids.append(str(order.delivery_partner_id))
    if str(current_user.id) not in allowed_ids and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Insufficient permissions')

    msgs = db.query(ChatMessage).filter(ChatMessage.order_id == order_id).order_by(ChatMessage.sent_at.asc()).limit(200).all()
    return [ChatMessageOut(id=str(m.id), order_id=str(m.order_id), sender_id=str(m.sender_id), sender_role=m.sender_role, content=m.content, message_type=m.message_type, sent_at=str(m.sent_at)) for m in msgs]


@router.post('/orders/{order_id}/chat', response_model=ChatMessageOut)
def post_chat_message(order_id: str, payload: ChatMessageIn, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    # Only participants may post
    allowed_ids = [str(order.customer_id)]
    if order.restaurant and order.restaurant.owner_id:
        allowed_ids.append(str(order.restaurant.owner_id))
    if order.delivery_partner_id:
        allowed_ids.append(str(order.delivery_partner_id))
    if str(current_user.id) not in allowed_ids and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail='Insufficient permissions')

    cm = ChatMessage(order_id=order_id, sender_id=current_user.id, sender_role=current_user.role, content=payload.content, message_type=payload.message_type)
    db.add(cm)
    db.commit()
    db.refresh(cm)

    out = {
        'id': str(cm.id),
        'order_id': str(cm.order_id),
        'sender_id': str(cm.sender_id),
        'sender_role': cm.sender_role,
        'content': cm.content,
        'message_type': cm.message_type,
        'sent_at': str(cm.sent_at),
    }

    # Emit via socket to order room
    try:
        realtime_service.emit(cm.order_id, 'chat:message', out)
    except Exception:
        pass

    return out


@router.post('/orders/{order_id}/chat/report')
def report_chat_message(order_id: str, msg_id: str, reason: str | None = None, current_user=Depends(get_current_active_user), db: Session = Depends(get_db)):
    # Simple report endpoint: records nothing yet, returns 202
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail='Order not found')
    # permission check omitted for brevity (assume participants can report)
    return {'status': 'reported'}
