from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request

from app.services import geocoding
import time
from collections import defaultdict

router = APIRouter()

# Simple in-memory per-client rate limiter for places endpoints (30 req/min)
# For production use a Redis-backed limiter shared across processes.
_places_rate_store: dict[str, list[float]] = defaultdict(list)
_PLACES_LIMIT = 30
_PLACES_WINDOW = 60


def _check_rate_limit(key: str):
    now = time.time()
    timestamps = _places_rate_store[key]
    # keep only timestamps within window
    timestamps[:] = [t for t in timestamps if now - t < _PLACES_WINDOW]
    if len(timestamps) >= _PLACES_LIMIT:
        return False
    timestamps.append(now)
    return True


@router.get("/autocomplete", summary="Proxy Google Places autocomplete")
def autocomplete(request: Request, input: str = Query(..., alias="input"), session_token: Optional[str] = None):
    client = request.client.host if request.client else "unknown"
    key = f"{client}:autocomplete"
    if not _check_rate_limit(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    try:
        result = geocoding.places_autocomplete(input, session_token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"predictions": result.get("predictions", []), "status": result.get("status")}


@router.get("/details", summary="Get place details by place_id")
def details(request: Request, place_id: str = Query(..., alias="place_id")):
    client = request.client.host if request.client else "unknown"
    key = f"{client}:details"
    if not _check_rate_limit(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    try:
        data = geocoding.place_details(place_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return data


@router.get("/reverse", summary="Reverse geocode lat/lng to address")
def reverse(request: Request, lat: float = Query(...), lng: float = Query(...)):
    client = request.client.host if request.client else "unknown"
    key = f"{client}:reverse"
    if not _check_rate_limit(key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests")

    try:
        data = geocoding.reverse_geocode(lat, lng)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return data
