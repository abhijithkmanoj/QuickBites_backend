import uuid
import pytest
from fastapi import status
from app.core.config import settings


def _register_and_login(client, email=None, role="restaurant_owner"):
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "name": "User",
        "email": email,
        "password": "Password123",
        "phone": "9876543210",
        "role": role,
    }
    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == status.HTTP_201_CREATED, register.text
    login = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == status.HTTP_200_OK, login.text
    return payload["email"], {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_update_tracking_success(client):
    email, headers = _register_and_login(client, role="restaurant_owner")

    restaurant_resp = client.post(
        "/api/v1/restaurants",
        headers=headers,
        json={
            "name": "Track Restaurant",
            "cuisine": "Indian",
            "address": "Street 1",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "delivery_time": 30,
            "description": "Track",
        },
    )
    assert restaurant_resp.status_code == status.HTTP_201_CREATED
    restaurant_id = restaurant_resp.json()["id"]

    menu_resp = client.post(
        "/api/v1/menu",
        headers=headers,
        json={
            "restaurant_id": restaurant_id,
            "name": "Curry",
            "description": "Hot",
            "price": 199.0,
            "category": "Main",
            "is_veg": True,
            "is_available": True,
        },
    )
    assert menu_resp.status_code == status.HTTP_201_CREATED
    menu_item_id = menu_resp.json()["id"]

    cart_resp = client.post(
        "/api/v1/cart/add",
        headers=headers,
        json={"restaurant_id": restaurant_id, "item": {"menu_item_id": menu_item_id, "name": "Curry", "price": 199.0, "quantity": 1}},
    )
    assert cart_resp.status_code == status.HTTP_201_CREATED

    order_resp = client.post(
        "/api/v1/orders",
        headers=headers,
        json={},
    )
    assert order_resp.status_code == status.HTTP_201_CREATED
    order_id = order_resp.json()["id"]

    partner_email, partner_headers = _register_and_login(client, role="delivery_partner")
    client.post(
        "/api/v1/delivery/register",
        headers=partner_headers,
        json={"vehicle_type": "Bike", "license_number": "DL222", "is_available": True},
    )

    assign_resp = client.post(
        "/api/v1/delivery/assign",
        headers=headers,
        json={"order_id": order_id},
    )
    assert assign_resp.status_code == status.HTTP_201_CREATED

    track_resp = client.post(
        f"/api/v1/delivery/order/{order_id}/location",
        headers=partner_headers,
        json={
            "partner_lat": 12.972,
            "partner_lng": 77.594,
            "delivery_lat": 12.9716,
            "delivery_lng": 77.5946,
        },
    )
    assert track_resp.status_code == status.HTTP_200_OK
    data = track_resp.json()
    assert data["partner_lat"] == 12.972
    assert data["partner_lng"] == 77.594
    assert data["delivery_lat"] == 12.9716
    assert data["delivery_lng"] == 77.5946


def test_get_tracking_success(client):
    email, headers = _register_and_login(client, role="restaurant_owner")

    restaurant_resp = client.post(
        "/api/v1/restaurants",
        headers=headers,
        json={
            "name": "Track2 Restaurant",
            "cuisine": "Indian",
            "address": "Street 2",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "delivery_time": 30,
            "description": "Track2",
        },
    )
    assert restaurant_resp.status_code == status.HTTP_201_CREATED
    restaurant_id = restaurant_resp.json()["id"]

    menu_resp = client.post(
        "/api/v1/menu",
        headers=headers,
        json={
            "restaurant_id": restaurant_id,
            "name": "Curry",
            "description": "Hot",
            "price": 199.0,
            "category": "Main",
            "is_veg": True,
            "is_available": True,
        },
    )
    assert menu_resp.status_code == status.HTTP_201_CREATED
    menu_item_id = menu_resp.json()["id"]

    cart_resp = client.post(
        "/api/v1/cart/add",
        headers=headers,
        json={"restaurant_id": restaurant_id, "item": {"menu_item_id": menu_item_id, "name": "Curry", "price": 199.0, "quantity": 1}},
    )
    assert cart_resp.status_code == status.HTTP_201_CREATED

    order_resp = client.post(
        "/api/v1/orders",
        headers=headers,
        json={},
    )
    assert order_resp.status_code == status.HTTP_201_CREATED
    order_id = order_resp.json()["id"]

    partner_email, partner_headers = _register_and_login(client, role="delivery_partner")
    client.post(
        "/api/v1/delivery/register",
        headers=partner_headers,
        json={"vehicle_type": "Bike", "license_number": "DL333", "is_available": True},
    )

    assign_resp = client.post(
        "/api/v1/delivery/assign",
        headers=headers,
        json={"order_id": order_id},
    )
    assert assign_resp.status_code == status.HTTP_201_CREATED

    track_resp = client.post(
        f"/api/v1/delivery/order/{order_id}/location",
        headers=partner_headers,
        json={
            "partner_lat": 12.972,
            "partner_lng": 77.594,
            "delivery_lat": 12.9716,
            "delivery_lng": 77.5946,
        },
    )
    assert track_resp.status_code == status.HTTP_200_OK

    get_resp = client.get(f"/api/v1/delivery/order/{order_id}/tracking", headers=headers)
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["route_distance_km"] is not None


def test_update_tracking_missing_coords(client):
    _, headers = _register_and_login(client, role="restaurant_owner")

    res = client.post(
        "/api/v1/delivery/order/not-a-uuid/location",
        headers=headers,
        json={"partner_lat": 12.9716},
    )
    assert res.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND)
