"""Firebase admin initialization helper.

Provides `init_firebase()` and `get_messaging()` helpers so other
services can import messaging without duplicating init logic.
"""
from __future__ import annotations

import os
import base64
import json
import logging

logger = logging.getLogger("app.services.firebase")


def _load_service_account():
    # Prefer explicit file path from settings if provided
    try:
        from app.core.config import settings

        path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None)
    except Exception:
        path = None

    if path and os.path.exists(path):
        return path

    b64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not b64:
        return None

    try:
        raw = base64.b64decode(b64)
        info = json.loads(raw)
        return info
    except Exception:
        logger.exception("Failed to decode FIREBASE_SERVICE_ACCOUNT_JSON")
        return None


def init_firebase():
    try:
        import firebase_admin
        from firebase_admin import credentials

        if firebase_admin._apps:
            return firebase_admin

        svc = _load_service_account()
        if not svc:
            logger.info("No Firebase service account configured; skipping firebase init")
            return None

        if isinstance(svc, str):
            cred = credentials.Certificate(svc)
        else:
            cred = credentials.Certificate(svc)

        # get project id from settings or service account
        try:
            from app.core.config import settings

            project_id = getattr(settings, "FIREBASE_PROJECT_ID", None) or svc.get("project_id")
        except Exception:
            project_id = svc.get("project_id") if isinstance(svc, dict) else None

        firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        return firebase_admin
    except Exception:
        logger.exception("Failed to initialize firebase_admin")
        return None


def get_messaging():
    try:
        app = init_firebase()
        if not app:
            return None
        from firebase_admin import messaging

        return messaging
    except Exception:
        logger.exception("Failed to get firebase messaging")
        return None
