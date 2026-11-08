import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.conversation import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(Message, session, tenant_id=tenant_id)

    async def save_message(
        self,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        sender_type: str,
        message_text: Optional[str] = None,
        mid: Optional[str] = None,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None,
        status: str = "sent",
        raw_payload: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Message:
        """
        Xabarni saqlash (kontakt, bot, ai yoki inson operator tomonidan).
        Agar 'mid' berilgan bo'lsa va allaqachon mavjud bo'lsa (Meta echo), dublikat yaratmaydi.
        """
        now = datetime.now(timezone.utc)
        if mid:
            stmt = (
                insert(Message)
                .values(
                    tenant_id=tenant_id,
                    conversation_id=conversation_id,
                    mid=mid,
                    sender_type=sender_type,
                    message_text=message_text,
                    media_url=media_url,
                    media_type=media_type,
                    status=status,
                    error_message=error_message,
                    raw_payload=raw_payload,
                    created_at=now
                )
                .on_conflict_do_nothing(index_elements=["mid"])
                .returning(Message)
            )
            res = await self.session.execute(stmt)
            saved = res.scalars().first()
            if saved:
                return saved

            # Mavjud xabarni topish
            fetch_stmt = select(Message).where(Message.tenant_id == tenant_id, Message.mid == mid)
            existing = await self.session.execute(fetch_stmt)
            return existing.scalars().one()
        else:
            msg = Message(
                tenant_id=tenant_id,
                conversation_id=conversation_id,
                mid=None,
                sender_type=sender_type,
                message_text=message_text,
                media_url=media_url,
                media_type=media_type,
                status=status,
                error_message=error_message,
                raw_payload=raw_payload,
                created_at=now
            )
            self.session.add(msg)
            await self.session.flush()
            return msg

    async def get_messages_by_conversation(
        self,
        tenant_id: uuid.UUID,
        conversation_id: uuid.UUID,
        limit: int = 50
    ) -> List[Message]:
        """Suhbatdagi xabarlar tarixini olish"""
        stmt = (
            select(Message)
            .where(Message.tenant_id == tenant_id, Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
