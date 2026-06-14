from fastapi import APIRouter
from app.api.api_v1.endpoints.admin_users import router as admin_router
from app.api.api_v1.endpoints.auth import router as auth_router
from app.api.api_v1.endpoints.delivery_partners import router as delivery_partners_router
from app.api.api_v1.endpoints.device_tokens import router as device_tokens_router
from app.api.api_v1.endpoints.health import router as health_router
from app.api.api_v1.endpoints.menus import router as menus_router
from app.api.api_v1.endpoints.cart import router as cart_router
from app.api.api_v1.endpoints.restaurants import router as restaurants_router
from app.api.api_v1.endpoints.addresses import router as addresses_router
from app.api.api_v1.endpoints.orders import router as orders_router
from app.api.api_v1.endpoints.welcome import router as welcome_router
from app.api.api_v1.endpoints.reviews import router as reviews_router
from app.api.api_v1.endpoints.recommendations import router as recommendations_router
from app.api.api_v1.endpoints.monitoring import router as monitoring_router
from app.api.api_v1.endpoints.users import router as users_router
from app.api.api_v1.endpoints.restaurant_owner import router as owner_router
from app.api.api_v1.endpoints.places import router as places_router
from app.api.api_v1.endpoints.notifications import router as notifications_router
from app.api.api_v1.endpoints.payouts import router as payouts_router
from app.api.api_v1.endpoints.loyalty import router as loyalty_router
from app.api.api_v1.endpoints.tracking import router as tracking_router
from app.api.api_v1.endpoints.promotions import router as promotions_router
from app.api.api_v1.endpoints.chat import router as chat_router
from app.api.api_v1.endpoints.ai_chat import router as ai_chat_router

router = APIRouter()
router.include_router(addresses_router, prefix="/addresses", tags=["addresses"])
router.include_router(orders_router, prefix="/orders", tags=["orders"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(restaurants_router, prefix="/restaurants", tags=["restaurants"])
router.include_router(menus_router, prefix="/menu", tags=["menu"])
router.include_router(cart_router, prefix="/cart", tags=["cart"])
router.include_router(delivery_partners_router, prefix="/delivery", tags=["delivery"])
router.include_router(welcome_router, prefix="/welcome", tags=["welcome"])
router.include_router(reviews_router, prefix="/reviews", tags=["reviews"])
router.include_router(device_tokens_router, prefix="/device-tokens", tags=["notifications"])
router.include_router(admin_router, prefix="/admin", tags=["admin"])
router.include_router(monitoring_router, prefix="/monitoring", tags=["monitoring"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(recommendations_router, prefix="/recommendations", tags=["recommendations"])
router.include_router(owner_router, prefix="/owner", tags=["owner"])
router.include_router(places_router, prefix="/places", tags=["places"])
router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
router.include_router(payouts_router, prefix="/payouts", tags=["payouts"])
router.include_router(loyalty_router, prefix="/loyalty", tags=["loyalty"])
router.include_router(tracking_router, prefix="/delivery", tags=["delivery"])
router.include_router(promotions_router, prefix="/promotions", tags=["promotions"])
router.include_router(chat_router, prefix="", tags=["chat"])
router.include_router(ai_chat_router, prefix="", tags=["ai-chat"]) 
