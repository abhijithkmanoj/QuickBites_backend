import uuid
from fastapi import status
from app.core.config import settings


def _register_and_login(client, email="owner@example.com", role="restaurant_owner"):
    # create unique email per call
    local, domain = email.split("@") if "@" in email else (email, "example.com")
    unique_email = f"{local}-{uuid.uuid4().hex[:8]}@{domain}"
    payload = {
        "name": "Restaurant Owner",
        "email": unique_email,
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


def test_personalized_recommendations_without_history(client):
    headers = _register_and_login(client, email="rec1@example.com", role="customer")
    resp = client.get("/api/v1/recommendations", headers=headers)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["type"] == "restaurant"
    assert isinstance(data["data"], list)


def test_recommendations_require_auth(client):
    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
