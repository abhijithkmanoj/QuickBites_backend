"""AI chatbot service for customer queries about restaurants, menu items, locations, etc.

Uses OpenRouter API (OpenAI-compatible) to provide natural-language answers
based on live database data.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"  # Fast, cheap, and widely available on OpenRouter


def _load_endpoint_documentation() -> str:
    try:
        root = Path(__file__).resolve().parents[2]
        endpoint_file = root / "endpoints_list.md"
        if endpoint_file.exists():
            return endpoint_file.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


_ENDPOINT_DOCUMENTATION = _load_endpoint_documentation()


def _gather_restaurant_context(db: Session) -> dict[str, Any]:
    """Collect all relevant restaurant data for AI context."""
    from app.db.models.menu_item import MenuItem
    from app.db.models.restaurant import Restaurant

    restaurants = db.query(Restaurant).filter(Restaurant.is_active == True).all()
    rows = []
    for r in restaurants:
        items = (
            db.query(MenuItem)
            .filter(MenuItem.restaurant_id == r.id, MenuItem.is_available == True)
            .all()
        )
        rows.append({
            "name": r.name,
            "cuisine": r.cuisine,
            "description": r.description,
            "address": r.address,
            "rating": r.rating,
            "delivery_time_minutes": r.delivery_time,
            "menu_items": [
                {
                    "name": i.name,
                    "category": i.category,
                    "description": i.description,
                    "price": i.price,
                    "is_veg": i.is_veg,
                }
                for i in items
            ],
        })
    return {"restaurants": rows}


# ── App feature documentation (embedded so the AI can guide users) ──────────

_APP_FEATURES = """
## QUICKBITES APP — COMPLETE FEATURE GUIDE

The AI assistant can answer questions about all app features, guide users on how to use them, and explain what actions to take. Below is the complete feature map.

---

### USER ROLES
- **customer**: Browse restaurants, place orders, track deliveries, write reviews
- **restaurant_owner**: Manage restaurant, menu items, incoming orders, dashboard
- **delivery_partner**: Onboard, accept deliveries, update location, complete orders
- **admin**: Manage users, restaurants, delivery partners, coupons, monitoring

### AUTHENTICATION
- **POST /api/v1/auth/register** — Register a new account (email, password, name, role)
  - Allowed roles during public registration: customer, restaurant_owner
  - Returns access_token + refresh_token (auto-login after registration)
- **POST /api/v1/auth/login** — Login with email + password
  - Accepts both JSON and form-encoded requests
  - Returns access_token + refresh_token + sets httpOnly cookie
- **POST /api/v1/auth/refresh** — Refresh an expired access_token using refresh_token
- **POST /api/v1/auth/logout** — Revoke refresh token and clear session
- **GET /api/v1/auth/me** — Get the currently authenticated user's profile
- **GET /api/v1/auth/admin-check** — Verify admin access

### RESTAURANTS
- **GET /api/v1/restaurants** — List restaurants with optional filters:
  - `search` (name, description, cuisine, address)
  - `cuisine` (filter by cuisine type)
  - `active` (default: true, only active restaurants)
  - `skip`, `limit` (pagination)
- **GET /api/v1/restaurants/search** — Search restaurants (alias with `q` param)
- **GET /api/v1/restaurants/nearby** — Find nearby restaurants by lat/lng + radius_km
- **GET /api/v1/restaurants/{id}** — Get detailed restaurant info
- **GET /api/v1/restaurants/{id}/menu** — List all menu items for a restaurant
- **POST /api/v1/restaurants** — Create a restaurant (restaurant_owner or admin)
- **PUT /api/v1/restaurants/{id}** — Update restaurant details (owner/admin)

### MENU ITEMS
- **POST /api/v1/menu** — Add a menu item to a restaurant (owner/admin)
- **PUT /api/v1/menu/{id}** — Update a menu item (owner/admin)
- **DELETE /api/v1/menu/{id}** — Delete a menu item (owner/admin)

### CART
- **GET /api/v1/cart** — View current user's cart with items
- **POST /api/v1/cart/add** — Add item to cart (requires restaurant_id + item details)
  - Tip: If cart has items from another restaurant, clear cart first
- **PUT /api/v1/cart/item/{item_id}** — Update item quantity
- **DELETE /api/v1/cart/item/{item_id}** — Remove item from cart
- **DELETE /api/v1/cart** — Clear entire cart

### ORDERS
- **POST /api/v1/orders** — Place an order from current cart
  - Supports address_id or delivery_address_text
  - payment_method: "cod" (default) or "card" (if payments enabled)
  - Optional promo_codes array
  - Awards loyalty points automatically
  - Sends push + in-app + email notifications
- **GET /api/v1/orders** — List user's orders (skip, limit)
- **GET /api/v1/orders/{id}** — Get order details
- **PUT /api/v1/orders/{id}/status** — Update order status (owner/admin)
  - Valid transitions: pending→accepted, accepted→preparing, preparing→ready_for_pickup, picked_up→delivered
- **PUT /api/v1/orders/{id}/cancel** — Cancel an order (customer only, must be pending/accepted)
- **PUT /api/v1/orders/{id}/accept** — Accept a pending order (owner)
- **PUT /api/v1/orders/{id}/reject** — Reject an order with optional reason (owner)
- **GET /api/v1/orders/{id}/tracking** — Get real-time delivery tracking data
- **POST /api/v1/delivery/order/{id}/location** — Update delivery partner GPS + ETA

### ADDRESSES
- **GET /api/v1/addresses** — List user's saved addresses
- **POST /api/v1/addresses** — Save a new address
- **PUT /api/v1/addresses/{id}** — Update an address
- **DELETE /api/v1/addresses/{id}** — Delete an address

### PAYMENTS (Stripe)
- **POST /api/v1/payments/intent** — Create a PaymentIntent
- **POST /api/v1/payments/confirm** — Confirm a payment
- **GET /api/v1/payments/methods** — List saved payment methods
- **POST /api/v1/payments/methods** — Save a payment method
- **DELETE /api/v1/payments/methods/{id}** — Remove a saved payment method
- **POST /api/v1/payments/refund** — Refund a payment
- **POST /api/v1/payments/webhook** — Stripe webhook endpoint
- Note: Payments must be enabled on the server (PAYMENTS_ENABLED=true)

### DELIVERY PARTNER
- **POST /api/v1/delivery/onboard** — Submit onboarding details (vehicle, license, aadhar)
- **GET /api/v1/delivery/profile** — Get delivery partner profile
- **PUT /api/v1/delivery/profile** — Update delivery partner profile
- **PUT /api/v1/delivery/availability** — Toggle availability (true/false)
- **GET /api/v1/delivery/available-orders** — List orders ready for pickup
- **POST /api/v1/delivery/assignments/{order_id}/accept** — Accept a delivery
- **PUT /api/v1/delivery/assignments/{order_id}/picked-up** — Mark as picked up
- **PUT /api/v1/delivery/assignments/{order_id}/delivered** — Mark as delivered
- **POST /api/v1/delivery/location** — Update current GPS location

### REVIEWS
- **POST /api/v1/reviews** — Submit a review (rating, comment, restaurant_id)
- **GET /api/v1/reviews** — Get reviews for a restaurant (query param: restaurant_id)

### FAVORITES (restaurants & menu items)
- **GET /api/v1/users/favorites** — List user's favorites (optional favorite_type filter)
- **POST /api/v1/users/favorites/add** — Add to favorites (favorite_type: restaurant/menu_item)
- **DELETE /api/v1/users/favorites/{id}** — Remove from favorites
- **GET /api/v1/users/favorites/check/{type}/{id}** — Check if item is favorited

### ACTIVITY LOG
- **GET /api/v1/users/activity** — View recent activity (paginated)
- **DELETE /api/v1/users/activity/{id}** — Delete a specific activity entry
- **POST /api/v1/users/activity/clear** — Clear old activities (older than N days)

### NOTIFICATIONS
- **GET /api/v1/notifications** — List notifications (paginated)
- **POST /api/v1/notifications/mark-read** — Mark notification(s) as read
- **POST /api/v1/device-tokens/register** — Register a device for push notifications
- **GET /api/v1/device-tokens/my-tokens** — List registered devices
- **DELETE /api/v1/device-tokens/{token}** — Remove a device token

### PROMOTIONS & COUPONS
- **GET /api/v1/promotions/active** — List active promotions
- **POST /api/v1/promotions/validate** — Validate promo code(s) against cart total
- **GET /api/v1/promotions/restaurants/{id}** — List promotions for a specific restaurant
- Admin endpoints for coupon CRUD: POST/GET/PATCH/DELETE /api/v1/admin/coupons

### LOYALTY REWARDS
- **GET /api/v1/loyalty/me** — Check current loyalty points balance
- **GET /api/v1/loyalty/rewards** — List available rewards to redeem
- **POST /api/v1/loyalty/redeem** — Redeem points for a reward
- Points are automatically awarded when orders are placed

### RECOMMENDATIONS
- **GET /api/v1/recommendations** — Get personalized recommendations
  - Optional: `menu_item_id` for similar food recommendations
  - Optional: `user_id` for user-specific recommendations

### ORDER CHAT (real-time messaging per order)
- **GET /api/v1/orders/{order_id}/chat** — View chat history for an order
- **POST /api/v1/orders/{order_id}/chat** — Send a chat message
- **POST /api/v1/orders/{order_id}/chat/report** — Report a chat message

### AI CHATBOT
- **POST /api/v1/ai-chat** — Ask a question (what you're using now)
- **GET /api/v1/ai-chat/history** — View your chat history
- **DELETE /api/v1/ai-chat/history** — Clear your chat history

### PLACES / GEOCODING
- **GET /api/v1/places/autocomplete** — Google Places autocomplete
- **GET /api/v1/places/details** — Get place details by place_id
- **GET /api/v1/places/reverse** — Reverse geocode lat/lng

### USER PROFILE & SETTINGS
- **GET /api/v1/users/profile** — View profile
- **PUT /api/v1/users/profile** — Update name, phone, bio, DOB, gender
- **POST /api/v1/users/profile-image** — Upload profile picture
- **DELETE /api/v1/users/profile-image** — Remove profile picture
- **GET /api/v1/users/settings** — View preferences (notifications, privacy, theme, language)
- **PUT /api/v1/users/settings** — Update preferences
- **POST /api/v1/users/change-password** — Change password (requires current password)
- **POST /api/v1/users/deactivate-account** — Deactivate account
- **GET /api/v1/users/order-history** — View order history with optional status filter

### RESTAURANT OWNER FEATURES
- **POST /api/v1/owner/onboard** — Submit owner onboarding (business name, documents)
- **GET /api/v1/owner/profile** — View owner profile
- **PUT /api/v1/owner/profile** — Update owner profile
- **GET /api/v1/owner/verification-status** — Check verification status
- **GET /api/v1/restaurants/owner/dashboard** — View dashboard with order counts and lists
  - Returns: incoming, active, completed orders + all owned restaurants
- Owner can: manage restaurants, menu items, accept/reject orders, update order status

### ADMIN FEATURES
- **GET /api/v1/admin/dashboard** — Dashboard stats (users, restaurants, orders, revenue)
- **GET/PATCH /api/v1/admin/users** — List/block/unblock users
- **GET/PATCH /api/v1/admin/restaurants** — List/approve/reject/suspend restaurants
- **GET/PATCH /api/v1/admin/owners** — List/approve/reject restaurant owner applications
- **GET/PATCH /api/v1/admin/partners** — List/approve/reject/suspend delivery partners
- **GET /api/v1/admin/orders** — List all orders
- **GET/DELETE /api/v1/admin/reviews** — List/remove reviews
- **CRUD /api/v1/admin/coupons** — Manage coupons
- **GET /api/v1/admin/monitoring/errors** — View recent errors
- **GET /api/v1/admin/monitoring/endpoints** — View endpoint usage stats

### TIPS & PAYOUTS
- **POST /api/v1/payouts/orders/{id}/tip** — Add a tip to an order
- **GET /api/v1/payouts/drivers/{id}/payouts** — View driver payouts
- **POST /api/v1/payouts/payouts/{id}/pay** — Mark payout as paid (admin)

### REAL-TIME FEATURES (WebSocket)
- Socket.IO at path `/socket.io/`
- Events: order status updates, delivery tracking, chat messages, notifications
- Auto-connects when user is logged in
"""


def _build_system_prompt(context: dict[str, Any]) -> str:
    """Build a system prompt with the restaurant data context and app feature knowledge."""
    restaurant_data = json.dumps(context, indent=2, ensure_ascii=False, default=str)
    endpoint_docs = (
        f"\n---\n### BACKEND ENDPOINT MAP\n{_ENDPOINT_DOCUMENTATION}"
        if _ENDPOINT_DOCUMENTATION
        else ""
    )
    return f"""You are QuickBites AI, a helpful restaurant assistant for the QuickBites food delivery app.

Your role is to:
1. Answer customer questions about restaurants, menu items, cuisines, pricing, locations, and availability.
2. Guide users on how to use all features of the QuickBites app — ordering, tracking, payments, profiles, etc.
3. Help restaurant owners and delivery partners with their specific workflows.
4. Explain what API endpoints to call for any action the user wants to take.

RULES:
- Answer ONLY based on the restaurant data, app features, and backend endpoint map documented below.
- Do not invent or refer to any API endpoints, pages, or features that are not listed here.
- If you don't know the answer, say so politely and suggest the customer explore the app or contact support.
- Be friendly, concise, and helpful.
- When suggesting dishes, mention the restaurant name and price.
- When users ask about how to do something (e.g., "how do I change my password?", "how do I become a delivery partner?"), guide them through the steps using the feature documentation.
- For app navigation questions, explain which page or section to visit.
- Keep responses under 200 words unless the user asks for more detail.

---

### CURRENT RESTAURANT DATA
Here is the current restaurant and menu data:

{restaurant_data}

---

### APP FEATURE DOCUMENTATION
Here is the complete documentation of all QuickBites app features that you can help users with:

{_APP_FEATURES}{endpoint_docs}
"""


def answer_question(db: Session, history: list | None = None) -> str:
    """Answer a customer's question using OpenRouter API and live DB data.

    Args:
        db: Database session.
        history: Optional list of recent AIChatMessage objects for conversation context.
        The last message in history should be the user's current question.
    """
    api_key = settings.OPENROUTER_API_KEY
    if not api_key:
        return "Sorry, the AI assistant is not configured yet. Please contact support."

    try:
        client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )

        context = _gather_restaurant_context(db)
        system_prompt = _build_system_prompt(context)

        # Build messages array with conversation history for context
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })

        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.9,
            extra_headers={
                "HTTP-Referer": "https://quickbites.app",
                "X-Title": "QuickBites AI Chat",
            },
        )

        reply = response.choices[0].message.content
        return reply.strip() if reply else "I couldn't generate an answer. Please try rephrasing your question."

    except Exception as e:
        error_str = str(e)
        logger.exception("AI chatbot error: %s", error_str)
        if "quota" in error_str.lower() or "insufficient_quota" in error_str.lower() or "rate_limit" in error_str.lower():
            return "The AI assistant has reached its usage limit. Please try again later or contact support to upgrade the API plan."
        return "Sorry, I encountered an issue processing your request. Please try again later."
