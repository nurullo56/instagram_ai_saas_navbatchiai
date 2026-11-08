import uuid
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.instagram import InstagramAccount
from app.repositories.base import BaseRepository


class InstagramAccountRepository(BaseRepository[InstagramAccount]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(InstagramAccount, session, tenant_id=tenant_id)

    async def get_by_ig_user_id(self, ig_user_id: str) -> Optional[InstagramAccount]:
        """Instagram Scoped ID (IGSID) orqali hisobni topish"""
        query = select(InstagramAccount).filter(
            InstagramAccount.ig_user_id == ig_user_id,
            InstagramAccount.is_active == True,
            InstagramAccount.deleted_at == None
        )
        query = self._apply_tenant_filter(query)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_active_accounts(self) -> List[InstagramAccount]:
        """Tenantga tegishli barcha faol hisoblarni olish"""
        query = select(InstagramAccount).filter(
            InstagramAccount.is_active == True,
            InstagramAccount.deleted_at == None
        )
        query = self._apply_tenant_filter(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def upsert_account(
        self,
        tenant_id: uuid.UUID,
        page_id: str,
        ig_user_id: str,
        username: str,
        name: Optional[str],
        profile_picture_url: Optional[str],
        encrypted_access_token: str,
        token_expires_at: datetime,
        webhook_subscribed: bool = False
    ) -> InstagramAccount:
        """Mavjud hisobni yangilash yoki yangisini yaratish (Upsert)"""
        existing = await self.get_by_ig_user_id(ig_user_id)
        if existing:
            existing.page_id = page_id
            existing.username = username
            existing.name = name
            existing.profile_picture_url = profile_picture_url
            existing.encrypted_access_token = encrypted_access_token
            existing.token_expires_at = token_expires_at
            existing.webhook_subscribed = webhook_subscribed
            existing.is_active = True
            existing.deleted_at = None
            await self.session.flush()
            return existing

        return await self.create(
            tenant_id=tenant_id,
            page_id=page_id,
            ig_user_id=ig_user_id,
            username=username,
            name=name,
            profile_picture_url=profile_picture_url,
            encrypted_access_token=encrypted_access_token,
            token_expires_at=token_expires_at,
            webhook_subscribed=webhook_subscribed,
            is_active=True
        )

    async def soft_delete(self, id: uuid.UUID) -> bool:
        """Akkauntni xavfsiz o'chirish (soft-delete, muloqot va audit izlarini saqlab qoladi)"""
        account = await self.get_by_id(id)
        if not account:
            return False
        account.is_active = False
        account.deleted_at = datetime.utcnow()
        await self.session.flush()
        return True
