import uuid
from typing import Optional, List, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant, TenantMembership
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(Tenant, session, tenant_id=tenant_id)

    async def get_by_slug(self, slug: str) -> Optional[Tenant]:
        query = select(Tenant).filter(Tenant.slug == slug)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_user_memberships(self, user_id: uuid.UUID) -> List[Tuple[Tenant, str]]:
        """Foydalanuvchiga tegishli barcha tenantlar va uning rollarini olish"""
        query = (
            select(Tenant, TenantMembership.role)
            .join(TenantMembership, Tenant.id == TenantMembership.tenant_id)
            .filter(TenantMembership.user_id == user_id, Tenant.is_active == True)
        )
        result = await self.session.execute(query)
        return list(result.all())

    async def get_membership(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[TenantMembership]:
        """Foydalanuvchining ma'lum bir tenantdagi a'zoligini tekshirish"""
        query = select(TenantMembership).filter(
            TenantMembership.user_id == user_id,
            TenantMembership.tenant_id == tenant_id
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def add_member(self, tenant_id: uuid.UUID, user_id: uuid.UUID, role: str = "member") -> TenantMembership:
        membership = TenantMembership(tenant_id=tenant_id, user_id=user_id, role=role)
        self.session.add(membership)
        await self.session.flush()
        return membership
