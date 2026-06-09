import os
from typing import Any, Dict, Optional

import httpx

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")


def _safe_get(d: dict, *keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def places_autocomplete(input_text: str, session_token: Optional[str] = None) -> Dict[str, Any]:
    """Proxy to Google Places Autocomplete.

    Returns a dict with 'predictions' key or raises RuntimeError on failure.
    """
    if not GOOGLE_PLACES_API_KEY:
        return {"predictions": [], "status": "API_KEY_MISSING"}

    params = {
        "input": input_text,
        "key": GOOGLE_PLACES_API_KEY,
    }
    if session_token:
        params["sessiontoken"] = session_token

    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Places autocomplete request failed: {exc}")

    return {"predictions": data.get("predictions", []), "status": data.get("status")}


def place_details(place_id: str) -> Dict[str, Any]:
    """Return lat/lng and formatted address for a given place_id."""
    if not GOOGLE_PLACES_API_KEY:
        return {"lat": None, "lng": None, "formatted_address": None, "place_id": None}

    params = {"place_id": place_id, "key": GOOGLE_PLACES_API_KEY, "fields": "geometry,formatted_address,place_id"}
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Place details request failed: {exc}")

    result = data.get("result") or {}
    geometry = result.get("geometry", {}).get("location", {})

    # Try to extract address components commonly returned by Google
    components = {c.get("types", [None])[0]: c for c in (result.get("address_components") or [])}

    def _comp_value(types):
        for t in types:
            for comp in (result.get("address_components") or []):
                if t in (comp.get("types") or []):
                    return comp.get("long_name")
        return None

    street = _comp_value(["street_address", "route"]) or result.get("formatted_address")
    city = _comp_value(["locality", "sublocality", "postal_town"]) or _comp_value(["administrative_area_level_2"]) or None
    state = _comp_value(["administrative_area_level_1"]) or None
    postal_code = _comp_value(["postal_code"]) or None

    return {
        "lat": _safe_get(geometry, "lat"),
        "lng": _safe_get(geometry, "lng"),
        "formatted_address": result.get("formatted_address"),
        "place_id": result.get("place_id"),
        "street": street,
        "city": city,
        "state": state,
        "postal_code": postal_code,
        "raw": result,
    }


def reverse_geocode(lat: float, lng: float) -> Dict[str, Any]:
    """Reverse geocode to human-readable address."""
    # Prefer Google Maps if API key is available, otherwise fall back to
    # Nominatim (OpenStreetMap) to avoid failing for users without a key.
    if GOOGLE_PLACES_API_KEY:
        params = {"latlng": f"{lat},{lng}", "key": GOOGLE_PLACES_API_KEY}
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        try:
            resp = httpx.get(url, params=params, timeout=5.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            # If Google request fails, fall back to Nominatim below
            data = None

        if data:
            results = data.get("results", [])
            if results:
                top = results[0]
                return {"formatted_address": top.get("formatted_address"), "place_id": top.get("place_id"), "raw": top}

    # Nominatim fallback (no API key or Google failed)
    try:
        nom_url = "https://nominatim.openstreetmap.org/reverse"
        nom_params = {"format": "jsonv2", "lat": lat, "lon": lng}
        headers = {"User-Agent": "QuickBites/1.0 (+https://example.com)"}
        resp = httpx.get(nom_url, params=nom_params, headers=headers, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Reverse geocode request failed: {exc}")

    formatted = data.get("display_name") or None
    place_id = data.get("place_id") or data.get("osm_id")
    return {"formatted_address": formatted, "place_id": place_id, "raw": data}


def geocode_address(address: str) -> Dict[str, Any]:
    """Geocode a freeform address string to lat/lng and formatted address."""
    if not GOOGLE_PLACES_API_KEY:
        return {"lat": None, "lng": None, "formatted_address": None, "place_id": None, "raw": {}}

    params = {"address": address, "key": GOOGLE_PLACES_API_KEY}
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    try:
        resp = httpx.get(url, params=params, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"Geocode request failed: {exc}")

    results = data.get("results", [])
    if not results:
        return {"lat": None, "lng": None, "formatted_address": None, "place_id": None, "raw": data}

    top = results[0]
    geometry = top.get("geometry", {}).get("location", {})
    return {
        "lat": geometry.get("lat"),
        "lng": geometry.get("lng"),
        "formatted_address": top.get("formatted_address"),
        "place_id": top.get("place_id"),
        "raw": top,
    }
