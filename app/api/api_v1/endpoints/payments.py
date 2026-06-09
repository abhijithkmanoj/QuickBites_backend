from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.db.models.payment import Payment
from app.db.models.user import User
from app.services import stripe_service
from app.db.models.payment_method import PaymentMethod
from app.db.models.payment import Payment as PaymentModel

router = APIRouter()


class PaymentIntentCreate(BaseModel):
    order_id: str | None = None
    amount: float
    currency: str = "inr"
    save_card: bool = False


class PaymentConfirm(BaseModel):
    payment_intent_id: str
    order_id: str | None = None


class PaymentMethodAttach(BaseModel):
    payment_method_id: str
    make_default: bool = False


class RefundRequest(BaseModel):
    payment_id: str
    amount_cents: int | None = None
    reason: str | None = None


@router.post("/intent")
def create_intent(
    payload: PaymentIntentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")

    # amount passed as rupees; convert to cents/paise
    try:
        amount_cents = int(round(payload.amount * 100))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid amount")

    try:
        intent = stripe_service.create_payment_intent(amount_cents, payload.currency, metadata={"user_id": str(current_user.id)})
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # persist a Payment record with Stripe ids
    payment = Payment(
        order_id=payload.order_id if payload.order_id else None,
        user_id=current_user.id,
        amount=payload.amount,
        amount_cents=amount_cents,
        method="card",
        status="pending",
        stripe_payment_intent_id=getattr(intent, "id", None),
        currency=payload.currency,
        stripe_customer_id=None,
        metadata={"save_card": payload.save_card},
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {"client_secret": intent.client_secret, "payment_id": str(payment.id), "payment_intent_id": intent.id}


@router.post("/confirm")
def confirm_payment(
    confirm_in: PaymentConfirm,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")
    try:
        intent = stripe_service.retrieve_payment_intent(confirm_in.payment_intent_id)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # Update local payment record if exists
    payment = db.query(PaymentModel).filter(PaymentModel.user_id == current_user.id, PaymentModel.status == "pending").order_by(PaymentModel.created_at.desc()).first()
    if payment:
        payment.status = "succeeded" if intent.status == "succeeded" else intent.status
        payment.stripe_payment_intent_id = intent.id
        db.add(payment)
        db.commit()
        db.refresh(payment)

    return {"success": intent.status == "succeeded", "order_id": confirm_in.order_id}


@router.get("/methods")
def list_methods(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")
    methods = db.query(PaymentMethod).filter(PaymentMethod.user_id == current_user.id).all()
    result = []
    for m in methods:
        result.append({
            "id": str(m.id),
            "stripe_payment_method_id": m.stripe_payment_method_id,
            "brand": m.card_brand,
            "last4": m.card_last4,
            "exp_month": m.card_exp_month,
            "exp_year": m.card_exp_year,
            "is_default": m.is_default,
        })
    return {"methods": result}


@router.post("/methods")
def attach_method(payload: PaymentMethodAttach, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")

    # find existing customer id
    existing = db.query(PaymentModel).filter(PaymentModel.user_id == current_user.id, PaymentModel.stripe_customer_id != None).first()
    if existing and existing.stripe_customer_id:
        customer_id = existing.stripe_customer_id
    else:
        try:
            customer_id = stripe_service.get_or_create_stripe_customer(current_user.email, description=str(current_user.id))
        except RuntimeError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
        # persist customer id on a Payment record for convenience
        pm_record = PaymentModel(user_id=current_user.id, amount=0.0, method="card", status="customer_created", stripe_customer_id=customer_id)
        db.add(pm_record)
        db.commit()

    try:
        pm = stripe_service.attach_payment_method_to_customer(payload.payment_method_id, customer_id)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

    # Save PaymentMethod locally
    card = getattr(pm, "card", None) or pm.get("card") if isinstance(pm, dict) else None
    pm_model = PaymentMethod(
        user_id=current_user.id,
        stripe_payment_method_id=payload.payment_method_id,
        stripe_customer_id=customer_id,
        type=getattr(pm, "type", None) or pm.get("type") if isinstance(pm, dict) else None,
        card_brand=(card.brand if card else card.get("brand") if isinstance(card, dict) else None),
        card_last4=(card.last4 if card else card.get("last4") if isinstance(card, dict) else None),
        card_exp_month=(card.exp_month if card else card.get("exp_month") if isinstance(card, dict) else None),
        card_exp_year=(card.exp_year if card else card.get("exp_year") if isinstance(card, dict) else None),
        is_default=payload.make_default,
    )
    db.add(pm_model)
    db.commit()
    db.refresh(pm_model)

    return {"id": str(pm_model.id), "stripe_payment_method_id": payload.payment_method_id}


@router.delete("/methods/{method_id}")
def detach_method(method_id: str, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")
    pm = db.query(PaymentMethod).filter(PaymentMethod.id == method_id, PaymentMethod.user_id == current_user.id).first()
    if not pm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found")
    try:
        stripe_service.detach_payment_method(pm.stripe_payment_method_id)
    except RuntimeError:
        # best-effort; continue to remove local record
        pass
    db.delete(pm)
    db.commit()
    return {"deleted": True}


@router.post("/refund")
def refund_payment(payload: RefundRequest, current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if not settings.PAYMENTS_ENABLED:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payments are disabled")
    payment = db.query(PaymentModel).filter(PaymentModel.id == payload.payment_id).first()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    # allow owner or admin (simple role check)
    if str(payment.user_id) != str(current_user.id) and getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to refund this payment")
    if not payment.stripe_payment_intent_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment has no Stripe intent")
    try:
        refund = stripe_service.create_refund(payment.stripe_payment_intent_id, amount_cents=payload.amount_cents, reason=payload.reason)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
    payment.status = "refunded"
    db.add(payment)
    db.commit()
    return {"refund": getattr(refund, "id", None) or refund.get("id") if isinstance(refund, dict) else None}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    # Stripe sends raw payload
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    try:
        event = stripe_service.construct_webhook_event(payload, sig)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # handle relevant events
    event_type = event["type"]
    data = event["data"]["object"]

    # Basic handling: payment_intent.succeeded / payment_intent.payment_failed
    if event_type == "payment_intent.succeeded":
        intent_id = data.get("id")
        # mark matching payment records as succeeded if payment with stripe_payment_intent_id exists
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            p = db.query(PaymentModel).filter(PaymentModel.stripe_payment_intent_id == intent_id).first()
            if p:
                p.status = "succeeded"
                db.add(p)
                db.commit()
        finally:
            db.close()
    return {"received": True}
