import uuid
from app.core.security import get_password_hash
from app.core.roles import Role
from app.db.models.restaurant import Restaurant
from app.db.models.user import User
from app.db.session import SessionLocal
from fastapi import status


def create_owner_and_restaurant():
    db = SessionLocal()
    password = "OwnerPassword123"
    unique_email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    owner = User(
        name="Owner User",
        email=unique_email,
        phone="5555555555",
        password_hash=get_password_hash(password),
        role=Role.restaurant_owner.value,
        is_active=True,
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)

    unique_rest = f"Owner Diner {uuid.uuid4().hex[:8]}"
    restaurant = Restaurant(
        owner_id=owner.id,
        name=unique_rest,
        description="Test restaurant for menu",
        cuisine="Italian",
        address="456 Menu St",
        latitude=41.0,
        longitude=-87.0,
        rating=4.7,
        delivery_time=25,
        is_active=True,
    )
    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)
    db.close()
    return owner, password, restaurant


def test_menu_item_crud_for_restaurant_owner(client):
    owner, password, restaurant = create_owner_and_restaurant()

    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": owner.email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    access_token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    create_payload = {
        "restaurant_id": str(restaurant.id),
        "category": "Main Course",
        "name": "Margherita Pizza",
        "description": "Classic cheese pizza",
        "price": 12.5,
        "image_url": "https://example.com/pizza.jpg",
        "is_veg": True,
        "is_available": True,
    }
    create_response = client.post("/api/v1/menu", json=create_payload, headers=headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    menu_item = create_response.json()
    assert menu_item["name"] == create_payload["name"]
    assert menu_item["restaurant_id"] == str(restaurant.id)
    assert menu_item["price"] == create_payload["price"]

    list_response = client.get(f"/api/v1/restaurants/{restaurant.id}/menu")
    assert list_response.status_code == status.HTTP_200_OK
    items = list_response.json()
    assert len(items) == 1
    assert items[0]["id"] == menu_item["id"]

    update_payload = {"price": 13.5, "is_available": False}
    update_response = client.put(f"/api/v1/menu/{menu_item['id']}", json=update_payload, headers=headers)
    assert update_response.status_code == status.HTTP_200_OK
    updated_item = update_response.json()
    assert updated_item["price"] == 13.5
    assert updated_item["is_available"] is False

    delete_response = client.delete(f"/api/v1/menu/{menu_item['id']}", headers=headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    confirm_response = client.get(f"/api/v1/restaurants/{restaurant.id}/menu")
    assert confirm_response.status_code == status.HTTP_200_OK
    assert confirm_response.json() == []
