from fastapi import APIRouter, Depends
from app.api.deps import get_settings

router = APIRouter()


@router.get("", summary="Health check")
def health_check(settings=Depends(get_settings)):
    return {"status": "ok", "service": settings.APP_NAME}
