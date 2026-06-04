
from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.crud.user import create_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token
from datetime import timedelta
import uuid
import requests

# Create database tables if they don't exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create a test user
test_email = f"test_{uuid.uuid4()}@example.com"
user_in = UserCreate(
    name="Test User",
    email=test_email,
    password="test123456",
    role="customer"
)
user = create_user(db, user_in)
print(f"Created user {user.email}")

# Create access token
access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
print(f"Created token: {access_token}")

# Now let's test adding to cart
# First let's create a restaurant and menu item (since we need those)
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem

test_restaurant = Restaurant(
    name="Test Restaurant",
    address="123 Test St",
    is_active=True
)
db.add(test_restaurant)
db.commit()
db.refresh(test_restaurant)

test_menu_item = MenuItem(
    restaurant_id=test_restaurant.id,
    name="Test Pizza",
    price=9.99,
    is_available=True
)
db.add(test_menu_item)
db.commit()
db.refresh(test_menu_item)

# Now let's make the request
base_url = "http://localhost:8000"
add_item_url = f"{base_url}/api/v1/cart/add"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
payload = {
    "restaurant_id": str(test_restaurant.id),
    "item": {
        "menu_item_id": str(test_menu_item.id),
        "name": "Test Pizza",
        "price": 9.99,
        "quantity": 1
    }
}

print(f"Making request to {add_item_url}")
response = requests.post(add_item_url, json=payload, headers=headers)
print(f"Response status: {response.status_code}")
print(f"Response: {response.text}")
