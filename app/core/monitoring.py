import logging
from collections import deque
from datetime import datetime
from typing import Deque, Dict

logger = logging.getLogger("app.monitoring")

MAX_EVENTS = 200
_recent_errors: Deque[dict] = deque(maxlen=MAX_EVENTS)
_endpoint_counts: Dict[str, int] = {}


def capture_event(kind: str, *, path: str, status_code: int, message: str, metadata: dict | None = None) -> None:
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "kind": kind,
        "path": path,
        "status_code": status_code,
        "message": message,
        "metadata": metadata or {},
    }
    _recent_errors.append(event)
    if status_code >= 500:
        logger.error("%s %s -> %s | %s", kind, path, status_code, message)
    elif status_code >= 400:
        logger.warning("%s %s -> %s | %s", kind, path, status_code, message)
    else:
        logger.info("%s %s -> %s | %s", kind, path, status_code, message)


def increment_request(path: str, status_code: int) -> None:
    _endpoint_counts[path] = _endpoint_counts.get(path, 0) + 1
    if status_code >= 400:
        capture_event("request_error", path=path, status_code=status_code, message="Client or server error")


def get_recent_errors(limit: int = 50) -> list[dict]:
    return list(_recent_errors)[-limit:]


def get_endpoint_counts() -> dict:
    return dict(sorted(_endpoint_counts.items(), key=lambda item: item[1], reverse=True))
