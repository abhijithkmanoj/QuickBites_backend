from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException

from app.api.deps import get_current_active_user

router = APIRouter()


@router.get("/", summary="Get user's notifications")
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_active_user),
):
    """Return paginated notifications for the current user (in-memory store).

    Note: this is a lightweight development implementation. Replace with DB-backed
    persistence for production.
    """
    # Prefer DB-backed notifications if available, else fall back to in-memory store
    try:
        from app.db.session import SessionLocal
        from app.crud.notification import list_user_notifications

        db = SessionLocal()
        try:
            rows = list_user_notifications(db, current_user.id, skip=skip, limit=limit)
            total = len(rows)
            payload = [
                {
                    "id": str(r.id),
                    "type": getattr(r, "type", None),
                    "title": getattr(r, "title", None),
                    "body": getattr(r, "body", None),
                    "order_id": str(r.order_id) if getattr(r, "order_id", None) else None,
                    "read": bool(getattr(r, "read", False)),
                    "created_at": r.created_at.isoformat() if getattr(r, "created_at", None) else None,
                }
                for r in rows
            ]
            return {"items": payload, "total": total, "skip": skip, "limit": limit}
        finally:
            db.close()
    except Exception:
        try:
            from app.services.notification_store import get_notifications

            items, total = get_notifications(current_user.id, skip=skip, limit=limit)
            payload = [
                {
                    "id": it["id"],
                    "type": it.get("type"),
                    "title": it.get("title"),
                    "body": it.get("body"),
                    "order_id": it.get("order_id"),
                    "read": bool(it.get("read")),
                    "created_at": it.get("created_at").isoformat() if it.get("created_at") else None,
                }
                for it in items
            ]
            return {"items": payload, "total": total, "skip": skip, "limit": limit}
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to fetch notifications")


from pydantic import BaseModel


class MarkReadRequest(BaseModel):
    notification_id: Optional[str] = None
    mark_all: Optional[bool] = False


@router.post("/mark-read", summary="Mark notification(s) read")
def mark_read(
    body: MarkReadRequest,
    current_user=Depends(get_current_active_user),
):
    try:
        from app.db.session import SessionLocal
        from app.crud.notification import mark_notification_read, mark_all_read as db_mark_all_read

        db = SessionLocal()
        try:
            if body.mark_all:
                changed = db_mark_all_read(db, current_user.id)
                return {"marked": changed}
            if not body.notification_id:
                raise HTTPException(status_code=400, detail="notification_id required unless mark_all is true")
            notif = mark_notification_read(db, current_user.id, body.notification_id)
            if not notif:
                raise HTTPException(status_code=404, detail="Notification not found")
            return {"marked": 1}
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception:
        # Fallback to in-memory store
        try:
            from app.services.notification_store import mark_read, mark_all_read

            if body.mark_all:
                changed = mark_all_read(current_user.id)
                return {"marked": changed}
            if not body.notification_id:
                raise HTTPException(status_code=400, detail="notification_id required unless mark_all is true")
            success = mark_read(current_user.id, body.notification_id)
            if not success:
                raise HTTPException(status_code=404, detail="Notification not found")
            return {"marked": 1}
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to mark notification read")
