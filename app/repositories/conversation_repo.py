import uuid
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(Conversation, session, tenant_id=tenant_id)

    async def get_by_recipient(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_recipient_id: str
    ) -> Optional[Conversation]:
        """Instagram foydalanuvchisi bilan suhbatni topish"""
        stmt = select(Conversation).where(
            Conversation.tenant_id == tenant_id,
            Conversation.instagram_account_id == instagram_account_id,
            Conversation.ig_recipient_id == ig_recipient_id
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_or_create(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_recipient_id: str,
        recipient_username: Optional[str] = None
    ) -> Conversation:
        """
        Suhbatni topish yoki yangi yaratish.
        Standart 24-soatlik Meta oynasi ochiladi.
        """
        now = datetime.now(timezone.utc)
        window_expires = now + timedelta(hours=24)

        stmt = (
            insert(Conversation)
            .values(
                tenant_id=tenant_id,
                instagram_account_id=instagram_account_id,
                ig_recipient_id=ig_recipient_id,
                recipient_username=recipient_username,
                status="open",
                mode="bot",
                last_message_at=now,
                messaging_window_expires_at=window_expires,
                unread_count=0
            )
            .on_conflict_do_nothing(
                index_elements=["tenant_id", "instagram_account_id", "ig_recipient_id"]
            )
            .returning(Conversation)
        )
        res = await self.session.execute(stmt)
        conversation = res.scalars().first()
        if conversation:
            return conversation

        # Agar mavjud bo'lsa, qaytarib olamiz
        existing = await self.get_by_recipient(tenant_id, instagram_account_id, ig_recipient_id)
        if not existing:
            raise RuntimeError("Conversation creation race condition failed to return record")
        return existing

    async def update_inbound_activity(
        self,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        recipient_username: Optional[str] = None
    ) -> Optional[Conversation]:
        """
        Foydalanuvchidan yangi xabar kelganda 24 soatlik oynani yangilash.
        """
        now = datetime.now(timezone.utc)
        window_expires = now + timedelta(hours=24)

        values = {
            "last_message_at": now,
            "messaging_window_expires_at": window_expires,
            "unread_count": Conversation.unread_count + 1
        }
        if recipient_username:
            values["recipient_username"] = recipient_username

        stmt = (
            update(Conversation)
            .where(Conversation.tenant_id == tenant_id, Conversation.id == conversation_id)
            .values(**values)
            .returning(Conversation)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def set_mode(
        self,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        mode: str
    ) -> bool:
        """Suhbat rejimini o'zgartirish: 'bot', 'human_takeover', 'ai_assistant'"""
        stmt = (
            update(Conversation)
            .where(Conversation.tenant_id == tenant_id, Conversation.id == conversation_id)
            .values(mode=mode)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0
