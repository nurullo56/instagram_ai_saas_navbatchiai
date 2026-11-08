from app.api.routers.auth import router as auth_router
from app.api.routers.tenants import router as tenants_router
from app.api.routers.instagram import router as instagram_router
from app.api.routers.webhooks import router as webhooks_router

__all__ = ["auth_router", "tenants_router", "instagram_router", "webhooks_router"]
