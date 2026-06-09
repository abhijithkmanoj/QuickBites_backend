from fastapi import status


def test_list_restaurants_returns_empty_list(client):
    response = client.get("/api/v1/restaurants")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_search_restaurants_returns_empty_list(client):
    response = client.get("/api/v1/restaurants/search?q=sushi")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_nearby_restaurants_requires_coordinates(client):
    response = client.get("/api/v1/restaurants/nearby")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_restaurant_requires_auth(client):
    payload = {
        "name": "Test Diner",
        "description": "A test restaurant",
        "cuisine": "American",
        "address": "123 Test Lane",
        "latitude": 40.0,
        "longitude": -74.0,
    }
    response = client.post("/api/v1/restaurants", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
