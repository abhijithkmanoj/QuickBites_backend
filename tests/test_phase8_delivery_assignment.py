from fastapi import status
from app.core.config import settings


def _register_and_login(client, email="owner@example.com", role="restaurant_owner"):
    payload = {
        "name": "Restaurant Owner",
        "email": email,
        "password": "Password123",
        "phone": "9876543210",
        "role": role,
    }
    register = client.post("/api/v1/auth/register", json=payload)
    assert register.status_code == status.HTTP_201_CREATED
    login = client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == status.HTTP_200_OK
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_assign_delivery_partner_success(client):
    headers = _register_and_login(client, role="restaurant_owner")

    restaurant_resp = client.post(
        "/api/v1/restaurants",
        headers=headers,
        json={
            "name": "Test Restaurant",
            "cuisine": "Indian",
            "address": "Test Address",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "delivery_time": 30,
            "description": "A test restaurant",
        },
    )
    assert restaurant_resp.status_code == status.HTTP_201_CREATED
    restaurant = restaurant_resp.json()
    restaurant_id = restaurant["id"]

    menu_resp = client.post(
        "/api/v1/menu",
        headers=headers,
        json={
            "restaurant_id": restaurant_id,
            "name": "Biryani",
            "description": "Tasty biryani",
            "price": 199.0,
            "category": "Main Course",
            "is_veg": True,
            "is_available": True,
        },
    )
    assert menu_resp.status_code == status.HTTP_201_CREATED
    menu_item = menu_resp.json()
    menu_item_id = menu_item["id"]

    cart_resp = client.post(
        "/api/v1/cart/add",
        headers=headers,
        json={"restaurant_id": restaurant_id, "item": {"menu_item_id": menu_item_id, "name": "Biryani", "price": 199.0, "quantity": 2}},
    )
    assert cart_resp.status_code == status.HTTP_201_CREATED

    order_resp = client.post(
        "/api/v1/orders",
        headers=headers,
        json={},
    )
    assert order_resp.status_code == status.HTTP_201_CREATED
    order = order_resp.json()
    order_id = order["id"]

    partner_headers = _register_and_login(
        client, email="partner1@example.com", role="delivery_partner"
    )
    client.post(
        "/api/v1/delivery/register",
        headers=partner_headers,
        json={"vehicle_type": "Bike", "license_number": "DL111", "is_available": True},
    )

    assign_resp = client.post(
        "/api/v1/delivery/assign",
        headers=headers,
        json={"order_id": order_id},
    )
    assert assign_resp.status_code == status.HTTP_201_CREATED

    order_check = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_check.status_code == status.HTTP_200_OK
    assert order_check.json()["delivery_partner_id"] is not None


def test_assign_partner_requires_auth(client):
    resp = client.post("/api/v1/delivery/assign", json={"order_id": "invalid"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED


def test_assign_partner_forbidden_for_customer(client):
    headers = _register_and_login(client, email="customer@example.com", role="customer")
    resp = client.post("/api/v1/delivery/assign", headers=headers, json={"order_id": "invalid"})
    assert resp.status_code == status.HTTP_403_FORBIDDEN

