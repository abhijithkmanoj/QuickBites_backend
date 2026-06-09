"""Stripe integration helpers.

Provides simple wrappers used by the API to create and confirm PaymentIntents.
Keep error handling simple: raise RuntimeError on Stripe failures so callers can convert to HTTP errors.
"""
from typing import Optional, Dict
import stripe

from app.core.config import settings


def init_stripe():
    if not settings.STRIPE_SECRET_KEY:
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_payment_intent(amount_cents: int, currency: str = "inr", metadata: Optional[Dict] = None) -> Dict:
    """Create a Stripe PaymentIntent and return the object dict.

    amount_cents: amount in smallest currency unit (e.g., paise / cents)
    """
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        intent = s.PaymentIntent.create(
            amount=amount_cents,
            currency=currency,
            metadata=metadata or {},
        )
        return intent
    except Exception as exc:
        raise RuntimeError(f"Stripe create_payment_intent failed: {exc}") from exc


def retrieve_payment_intent(intent_id: str) -> Dict:
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        return s.PaymentIntent.retrieve(intent_id)
    except Exception as exc:
        raise RuntimeError(f"Stripe retrieve_payment_intent failed: {exc}") from exc


def construct_webhook_event(payload: bytes, sig_header: str):
    s = init_stripe()
    if not s or not settings.STRIPE_WEBHOOK_SECRET:
        raise RuntimeError("Stripe webhook is not configured")
    try:
        return s.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=settings.STRIPE_WEBHOOK_SECRET)
    except Exception as exc:
        raise RuntimeError(f"Stripe webhook signature verification failed: {exc}") from exc


def get_or_create_stripe_customer(user_email: str, description: str | None = None) -> str:
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        # Create a customer; callers should persist id
        cust = s.Customer.create(email=user_email, description=description or "")
        return cust.id
    except Exception as exc:
        raise RuntimeError(f"Stripe create customer failed: {exc}") from exc


def create_refund(payment_intent_id: str, amount_cents: int | None = None, reason: str | None = None):
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        # Retrieve Charge from PaymentIntent
        intent = s.PaymentIntent.retrieve(payment_intent_id)
        charges = intent.charges.data if hasattr(intent, "charges") else []
        if not charges:
            raise RuntimeError("No charge found for PaymentIntent")
        charge_id = charges[0].id
        refund = s.Refund.create(charge=charge_id, amount=amount_cents, reason=reason)
        return refund
    except Exception as exc:
        raise RuntimeError(f"Stripe create refund failed: {exc}") from exc


def attach_payment_method_to_customer(payment_method_id: str, customer_id: str):
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        pm = s.PaymentMethod.attach(payment_method_id, customer=customer_id)
        return pm
    except Exception as exc:
        raise RuntimeError(f"Stripe attach payment method failed: {exc}") from exc


def detach_payment_method(payment_method_id: str):
    s = init_stripe()
    if not s:
        raise RuntimeError("Stripe is not configured")
    try:
        pm = s.PaymentMethod.detach(payment_method_id)
        return pm
    except Exception as exc:
        raise RuntimeError(f"Stripe detach payment method failed: {exc}") from exc
