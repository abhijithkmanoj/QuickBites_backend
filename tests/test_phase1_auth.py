from fastapi import status
from app.core.config import settings


def test_register_login_me_refresh_logout(client):
    user_payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "Password123",
        "phone": "1234567890",
    }

    # Register a new user
    register_response = client.post("/api/v1/auth/register", json=user_payload)
    assert register_response.status_code == status.HTTP_201_CREATED
    user_data = register_response.json()
    assert user_data["email"] == user_payload["email"]
    assert user_data["name"] == user_payload["name"]
    assert user_data["role"] == "customer"

    # Login with the registered user
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    assert token_data["access_token"]
    assert token_data["refresh_token"]
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]

    # Access protected /me route with bearer token
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == status.HTTP_200_OK
    me_data = me_response.json()
    assert me_data["email"] == user_payload["email"]
    assert me_data["name"] == user_payload["name"]

    # Refresh access token using the refresh cookie
    refresh_response = client.post("/api/v1/auth/refresh")
    assert refresh_response.status_code == status.HTTP_200_OK
    refresh_data = refresh_response.json()
    assert refresh_data["access_token"]
    assert refresh_data["refresh_token"]
    assert refresh_data["access_token"] != access_token

    # Logout should clear refresh cookie
    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == status.HTTP_200_OK
    assert settings.REFRESH_TOKEN_COOKIE_NAME not in client.cookies

    # Refresh should now fail without a refresh cookie
    refresh_after_logout = client.post("/api/v1/auth/refresh")
    assert refresh_after_logout.status_code == status.HTTP_400_BAD_REQUEST


def test_protected_route_requires_auth(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_duplicate_registration_is_rejected(client):
    user_payload = {
        "name": "Duplicate User",
        "email": "duplicate@example.com",
        "password": "Password123",
        "phone": "0987654321",
    }

    first_response = client.post("/api/v1/auth/register", json=user_payload)
    assert first_response.status_code == status.HTTP_201_CREATED

    second_response = client.post("/api/v1/auth/register", json=user_payload)
    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    assert second_response.json()["detail"] == "A user with this email already exists."
