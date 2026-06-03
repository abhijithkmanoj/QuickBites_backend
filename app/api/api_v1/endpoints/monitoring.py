from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.roles import Role
from app.db.models.user import User
from app.core.monitoring import get_recent_errors, get_endpoint_counts

router = APIRouter()


@router.get("/errors", summary="Get recent error events")
def recent_errors(
    limit: int = 50,
    current_user: User = Depends(require_roles(Role.admin)),
):
    return get_recent_errors(limit=limit)


@router.get("/endpoints", summary="Get endpoint usage counts")
def endpoint_stats(
    current_user: User = Depends(require_roles(Role.admin)),
):
    return get_endpoint_counts()
