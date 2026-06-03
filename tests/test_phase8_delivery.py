from fastapi import status
from app.core.config import settings


def test_delivery_partner_register_profile_availability(client):
    user_payload = {
        "name": "Delivery Partner User",
        "email": "partner@example.com",
        "password": "Password123",
        "phone": "9876543210",
        "role": "delivery_partner",
    }

    register_response = client.post("/api/v1/auth/register", json=user_payload)
    assert register_response.status_code == status.HTTP_201_CREATED

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    profile_before = client.get("/api/v1/delivery/profile", headers=headers)
    assert profile_before.status_code == status.HTTP_404_NOT_FOUND

    register_partner = client.post(
        "/api/v1/delivery/register",
        headers=headers,
        json={"vehicle_type": "Bike", "license_number": "DL123456", "is_available": True},
    )
    assert register_partner.status_code == status.HTTP_201_CREATED
    partner_data = register_partner.json()
    assert partner_data["vehicle_type"] == "Bike"
    assert partner_data["license_number"] == "DL123456"
    assert partner_data["is_available"] is True

    duplicate_register = client.post(
        "/api/v1/delivery/register",
        headers=headers,
        json={"vehicle_type": "Scooter", "license_number": "DL654321"},
    )
    assert duplicate_register.status_code == status.HTTP_400_BAD_REQUEST

    profile_after = client.get("/api/v1/delivery/profile", headers=headers)
    assert profile_after.status_code == status.HTTP_200_OK
    assert profile_after.json()["vehicle_type"] == "Bike"

    update_availability = client.put(
        "/api/v1/delivery/availability",
        headers=headers,
        json={"is_available": False},
    )
    assert update_availability.status_code == status.HTTP_200_OK
    assert update_availability.json()["is_available"] is False

    unauthorized = client.get("/api/v1/delivery/profile")
    assert unauthorized.status_code == status.HTTP_401_UNAUTHORIZED
