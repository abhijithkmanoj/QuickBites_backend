import logging
import os
import base64
import json
from typing import Any, Iterable

logger = logging.getLogger("app.notifications.firebase")


class FirebaseNotificationService:
    @staticmethod
    def _ensure_app_initialized():
        """Initialize firebase_admin if not already initialized.

        Supports either a file path in settings.FIREBASE_CREDENTIALS_PATH
        or a base64-encoded JSON in env var `FIREBASE_SERVICE_ACCOUNT_JSON`.
        """
        try:
            import firebase_admin
            from firebase_admin import credentials

            if firebase_admin._apps:
                return

            # Prefer explicit credentials path from settings if provided
            try:
                from app.core.config import settings

                cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
                project_id = getattr(settings, "FIREBASE_PROJECT_ID", None)
            except Exception:
                cred_path = None
                project_id = None

            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
            else:
                # Fallback to base64-encoded service account JSON env var
                b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
                if not b64:
                    logger.info("No Firebase credentials provided; skipping initialization.")
                    return
                try:
                    raw = base64.b64decode(b64)
                    info = json.loads(raw)
                    cred = credentials.Certificate(info)
                    # If project id not set in settings, try to populate from JSON
                    if not project_id:
                        project_id = info.get("project_id")
                except Exception:
                    logger.exception("Failed to decode FIREBASE_SERVICE_ACCOUNT_JSON")
                    return

            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        except Exception:
            logger.exception("Failed to initialize firebase_admin")

    @staticmethod
    def send_notification(tokens: Iterable[str], title: str, body: str, data: dict[str, Any] | None = None) -> None:
        from app.db.session import SessionLocal
        from app.crud.device_token import delete_device_token

        tokens = [t for t in tokens if t]
        if not tokens:
            logger.debug("No device tokens to send notification: %s", title)
            return

        try:
            FirebaseNotificationService._ensure_app_initialized()
            import firebase_admin
            from firebase_admin import messaging

            if not firebase_admin._apps:
                logger.info("firebase_admin not initialized; skipping push send")
                return

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data={k: str(v) for k, v in (data or {}).items()},
                tokens=list(tokens),
            )
            response = messaging.send_multicast(message)
            logger.info("Firebase notification sent: %s successes, %s failures", response.success_count, response.failure_count)

            # Clean up unregistered tokens
            if response.failure_count:
                db = SessionLocal()
                try:
                    for idx, resp in enumerate(response.responses):
                        if not resp.success:
                            ex = getattr(resp, "exception", None)
                            token = list(tokens)[idx]
                            msg = str(ex) if ex is not None else ""
                            if "registration-token-not-registered" in msg or "NotRegistered" in msg or "InvalidRegistrationToken" in msg:
                                try:
                                    delete_device_token(db, token)
                                    logger.info("Deleted unregistered device token: %s", token)
                                except Exception:
                                    logger.exception("Failed to delete token: %s", token)
                finally:
                    db.close()
        except Exception:
            logger.exception("Failed to send Firebase notification: %s", title)

    @staticmethod
    def send_order_notification(order_id: str, user_ids: Iterable[str], title: str, body: str) -> None:
        from app.db.session import SessionLocal
        from app.db.models.device_token import DeviceToken

        db = SessionLocal()
        try:
            rows = (
                db.query(DeviceToken.token)
                .filter(DeviceToken.user_id.in_(list(user_ids)))
                .all()
            )
            tokens = [row.token for row in rows]
            FirebaseNotificationService.send_notification(tokens, title=title, body=body, data={"order_id": order_id})
        finally:
            db.close()
