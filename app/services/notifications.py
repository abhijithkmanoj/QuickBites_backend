"""Async notification orchestrator.

Provides lightweight async wrappers and event->template mapping for
order-related notifications. Uses the existing synchronous
`FirebaseNotificationService` under the hood but runs blocking calls
in a thread so endpoints can await without blocking the event loop.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

logger = logging.getLogger("app.services.notifications")


async def send_push(user_id: int | str, title: str, body: str, data: dict | None = None) -> None:
    """Fetch user's device tokens and send a push notification.

    This is async but delegates the blocking firebase call to a thread.
    Failures are logged and swallowed — notifications must never raise.
    """
    try:
        from app.db.session import SessionLocal
        from app.crud.device_token import get_user_device_tokens
        from app.services.firebase_notifications import FirebaseNotificationService

        db = SessionLocal()
        try:
            rows = get_user_device_tokens(db, user_id)
            tokens = [r.token for r in rows if getattr(r, "token", None)]
        finally:
            db.close()

        if not tokens:
            logger.debug("No device tokens for user %s", user_id)
            return

        # Run the blocking send in a threadpool
        await asyncio.to_thread(
            FirebaseNotificationService.send_notification,
            tokens,
            title,
            body,
            data,
        )
    except Exception:
        logger.exception("Error while sending push to user %s", user_id)


async def send_order_notification(order_id: str | int, event: str) -> None:
    """Map an order event to templates and notify relevant users.

    Supported events: order_placed, order_accepted, order_ready,
    out_for_delivery, order_delivered, order_cancelled
    """
    try:
        from app.db.session import SessionLocal
        from app.crud.order import get_order
        from app.services.firebase_notifications import FirebaseNotificationService
        from app.services import realtime as realtime_service

        templates = {
            "order_placed": ("Order Confirmed 🎉", "Your order #{id} has been placed."),
            "order_accepted": ("Restaurant is preparing your order", "Order #{id} is being prepared."),
            "order_ready": ("Order Ready for Pickup", "Order #{id} is ready for pickup."),
            "out_for_delivery": ("Out for Delivery 🛵", "Your order #{id} is out for delivery."),
            "order_delivered": ("Delivered! 🎉", "Your order #{id} has been delivered."),
            "order_cancelled": ("Order Cancelled", "Your order #{id} was cancelled."),
        }

        db = SessionLocal()
        try:
            order = get_order(db, order_id)
        finally:
            db.close()

        if not order:
            logger.debug("Order not found for notification: %s", order_id)
            return

        title_tpl, body_tpl = templates.get(event, ("Order Update", "Your order #{id} has an update."))
        title = title_tpl.replace("{id}", str(order.id))
        body = body_tpl.replace("{id}", str(order.id))

        user_ids: list[str] = [str(order.customer_id)]
        if order.restaurant and getattr(order.restaurant, "owner_id", None):
            user_ids.append(str(order.restaurant.owner_id))
        if getattr(order, "delivery_partner_id", None):
            user_ids.append(str(order.delivery_partner_id))

        # Send pushes concurrently (fire-and-forget style)
        tasks = [send_push(uid, title, body, data={"order_id": str(order.id)}) for uid in user_ids]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Also emit in-app socket notifications
        try:
            realtime_service.emit_notification_to_users(user_ids, {
                "type": event,
                "title": title,
                "body": body,
                "order_id": str(order.id),
            })
            # Persist a server-side notification record: prefer DB, fallback to in-memory
            try:
                from app.db.session import SessionLocal
                from app.crud.notification import create_notification

                db = SessionLocal()
                try:
                    for uid in user_ids:
                        try:
                            create_notification(
                                db,
                                uid,
                                type=event,
                                title=title,
                                body=body,
                                data={"order_id": str(order.id)},
                                order_id=order.id,
                            )
                        except Exception:
                            logger.exception("Failed to create DB notification for user %s", uid)
                finally:
                    db.close()
            except Exception:
                # DB not available or failed — fall back to in-memory store
                try:
                    from app.services.notification_store import add_notification

                    for uid in user_ids:
                        add_notification(uid, {
                            "type": event,
                            "title": title,
                            "body": body,
                            "order_id": str(order.id),
                        })
                except Exception:
                    logger.exception("Failed to persist in-memory notification for order %s", order.id)
        except Exception:
            logger.exception("Failed to emit realtime notification for order %s", order.id)

    except Exception:
        logger.exception("Failed to process order notification for %s / %s", order_id, event)
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("app.notifications")


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    body: str
    html: Optional[str] = None
    from_email: Optional[str] = None


class EmailService:
    @staticmethod
    def send_email(message: EmailMessage) -> bool:
        from app.core.config import settings

        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            logger.info("Email not configured, skipping send to %s: %s", message.to_email, message.subject)
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = message.from_email or settings.SMTP_FROM_EMAIL
            msg["To"] = message.to_email

            msg.attach(MIMEText(message.body, "plain"))
            if message.html:
                msg.attach(MIMEText(message.html, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Email sent to %s: %s", message.to_email, message.subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", message.to_email)
            return False

    @staticmethod
    def send_registration_email(to_email: str, name: str) -> None:
        subject = "Welcome to QuickBites!"
        body = f"Hi {name},\n\nWelcome to QuickBites. Your account has been created successfully."
        html = f"<h1>Welcome to QuickBites!</h1><p>Hi {name}, your account has been created.</p>"
        EmailService.send_email(EmailMessage(to_email=to_email, subject=subject, body=body, html=html))

    @staticmethod
    def send_order_confirmation(to_email: str, order_id: str, total_amount: float) -> None:
        subject = f"Order Confirmed - {order_id}"
        body = f"Your order {order_id} has been confirmed. Total: ₹{total_amount}"
        html = f"<h1>Order Confirmed</h1><p>Order ID: {order_id}</p><p>Total: ₹{total_amount}</p>"
        EmailService.send_email(EmailMessage(to_email=to_email, subject=subject, body=body, html=html))

    @staticmethod
    def send_payment_confirmation(to_email: str, order_id: str, amount: float, method: str) -> None:
        subject = f"Payment Confirmed - {order_id}"
        body = f"Payment of ₹{amount} received via {method} for order {order_id}."
        html = f"<h1>Payment Confirmed</h1><p>Order ID: {order_id}</p><p>Amount: ₹{amount}</p><p>Method: {method}</p>"
        EmailService.send_email(EmailMessage(to_email=to_email, subject=subject, body=body, html=html))
