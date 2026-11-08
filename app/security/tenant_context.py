from contextvars import ContextVar
from typing import Optional
from uuid import UUID

# Har bir asinxron so'rov uchun alohida tenant identifikatori
_tenant_context: ContextVar[Optional[UUID]] = ContextVar("current_tenant_id", default=None)


def set_current_tenant_id(tenant_id: Optional[UUID]) -> None:
    """Joriy asinxron task uchun tenant ID ni o'rnatish"""
    _tenant_context.set(tenant_id)


def get_current_tenant_id() -> Optional[UUID]:
    """Joriy asinxron taskdan tenant ID ni olish"""
    return _tenant_context.get()
