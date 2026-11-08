from app.api.routers.auth import router as auth_router
from app.api.routers.tenants import router as tenants_router

__all__ = ["auth_router", "tenants_router"]
