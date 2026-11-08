import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instagram import InstagramAccount
from app.repositories.instagram_repo import InstagramAccountRepository
from app.integrations.meta.oauth import MetaOAuthService
from app.security.encryption import token_encryption
from app.config.logging import logger


class InstagramService:
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        self.session = session
        self.tenant_id = tenant_id
        self.repo = InstagramAccountRepository(session, tenant_id=tenant_id)
        self.oauth_service = MetaOAuthService()

    def get_oauth_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Meta OAuth login oynasi havolasini olish"""
        return self.oauth_service.get_authorization_url(redirect_uri, state)

    async def connect_accounts_from_oauth(
        self,
        tenant_id: uuid.UUID,
        code: str,
        redirect_uri: str
    ) -> List[InstagramAccount]:
        """
        Meta OAuth kodi orqali tokenlarni olish, ularni AES-256-GCM bilan shifrlash,
        sahifani webhooklarga obuna qilish va bazaga saqlash.
        """
        # 1. Short-lived token
        token_data = await self.oauth_service.exchange_code_for_short_lived_token(code, redirect_uri)
        short_lived_token = token_data.get("access_token")
        if not short_lived_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Meta Access Token olinmadi")

        # 2. Long-lived token (60 kunlik)
        long_lived_data = await self.oauth_service.exchange_for_long_lived_token(short_lived_token)
        long_lived_token = long_lived_data.get("access_token") or short_lived_token
        expires_in = long_lived_data.get("expires_in", 60 * 24 * 3600)  # Default 60 kun
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # 3. Bog'langan Instagram akkauntlarni olish
        pages_and_accounts = await self.oauth_service.get_managed_pages_and_instagram_accounts(long_lived_token)
        if not pages_and_accounts:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ushbu Facebook hisobiga bog'langan Instagram Professional (Business/Creator) akkaunt topilmadi."
            )

        saved_accounts = []
        for item in pages_and_accounts:
            # Tokenni AES-256-GCM bilan shifrlash
            page_token = item["page_access_token"]
            encrypted_token = token_encryption.encrypt(page_token)

            # Webhookka obuna qilish
            webhook_subscribed = False
            try:
                webhook_subscribed = await self.oauth_service.subscribe_page_to_webhooks(
                    page_id=item["page_id"],
                    page_access_token=page_token
                )
            except Exception as e:
                logger.error("Sahifani webhookka ulashda xato", page_id=item["page_id"], error=str(e))

            # Bazaga saqlash (Upsert)
            account = await self.repo.upsert_account(
                tenant_id=tenant_id,
                page_id=item["page_id"],
                ig_user_id=item["ig_user_id"],
                username=item["ig_username"],
                name=item["ig_name"],
                profile_picture_url=item["ig_profile_picture_url"],
                encrypted_access_token=encrypted_token,
                token_expires_at=token_expires_at,
                webhook_subscribed=webhook_subscribed
            )
            saved_accounts.append(account)

        await self.session.commit()
        logger.info("Instagram hisoblari muvaffaqiyatli saqlandi", tenant_id=str(tenant_id), count=len(saved_accounts))
        return saved_accounts

    async def get_tenant_accounts(self) -> List[InstagramAccount]:
        """Tenantning faol hisoblari ro'yxati"""
        return await self.repo.get_active_accounts()

    async def disconnect_account(self, account_id: uuid.UUID) -> bool:
        """Akkauntni uzish / soft-delete qilish"""
        account = await self.repo.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instagram akkaunt topilmadi")
        result = await self.repo.soft_delete(account_id)
        await self.session.commit()
        return result
