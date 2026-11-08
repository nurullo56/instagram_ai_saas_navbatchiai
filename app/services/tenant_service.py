import uuid
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.tenant import Tenant
from app.repositories.tenant_repo import TenantRepository


class TenantService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tenant_repo = TenantRepository(session)

    async def get_user_tenants(self, user_id: uuid.UUID) -> List[Tuple[Tenant, str]]:
        """Foydalanuvchining barcha tenantlari va rollarini olish"""
        return await self.tenant_repo.get_user_memberships(user_id)

    async def verify_tenant_access(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
        """Foydalanuvchining ko'rsatilgan tenantga kirish huquqini tekshirish"""
        membership = await self.tenant_repo.get_membership(user_id, tenant_id)
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sizda ushbu tenant ma'lumotlariga kirish huquqi yo'q"
            )
        return membership.role
