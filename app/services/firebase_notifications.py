import logging
from typing import Any

logger = logging.getLogger("app.notifications.firebase")


class FirebaseNotificationService:
    @staticmethod
    def send_notification(tokens: list[str], title: str, body: str, data: dict[str, Any] | None = None) -> None:
        from app.core.config import settings

        if not settings.FIREBASE_CREDENTIALS_PATH or not tokens:
            logger.info("Firebase not configured or no tokens; skipping notification: %s", title)
            return

        try:
            import firebase_admin
            from firebase_admin import messaging

            if not firebase_admin._apps:
                firebase_admin.initialize_app(
                    firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH),
                    {"projectId": settings.FIREBASE_PROJECT_ID},
                )

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=tokens,
            )
            response = messaging.send_multicast(message)
            logger.info("Firebase notification sent: %s successes, %s failures", response.success_count, response.failure_count)
        except Exception:
            logger.exception("Failed to send Firebase notification: %s", title)

    @staticmethod
    def send_order_notification(order_id: str, user_ids: list[str], title: str, body: str) -> None:
        from app.db.session import SessionLocal
        from app.db.models.device_token import DeviceToken

        db = SessionLocal()
        try:
            tokens = (
                db.query(DeviceToken.token)
                .filter(DeviceToken.user_id.in_(user_ids))
                .all()
            )
            FirebaseNotificationService.send_notification(
                [row.token for row in tokens],
                title=title,
                body=body,
                data={"order_id": order_id},
            )
        finally:
            db.close()
