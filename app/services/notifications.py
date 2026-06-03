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
