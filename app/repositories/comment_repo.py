import uuid
from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.comment import CommentLog
from app.repositories.base import BaseRepository


class CommentRepository(BaseRepository[CommentLog]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(CommentLog, session, tenant_id=tenant_id)

    async def upsert_comment(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_comment_id: str,
        ig_media_id: str,
        ig_user_id: str,
        comment_text: str,
        ig_comment_created_at: datetime
    ) -> CommentLog:
        """
        Instagram izohini bazaga kiritish yoki mavjud bo'lsa uni qaytarish.
        ON CONFLICT DO NOTHING orqali dublikat yaratilmaydi.
        """
        stmt = (
            insert(CommentLog)
            .values(
                tenant_id=tenant_id,
                instagram_account_id=instagram_account_id,
                ig_comment_id=ig_comment_id,
                ig_media_id=ig_media_id,
                ig_user_id=ig_user_id,
                comment_text=comment_text,
                ig_comment_created_at=ig_comment_created_at,
                private_reply_status="none",
                private_reply_lease_version=1
            )
            .on_conflict_do_nothing(index_elements=["tenant_id", "ig_comment_id"])
            .returning(CommentLog)
        )
        res = await self.session.execute(stmt)
        record = res.scalars().first()
        if record:
            return record

        # Agar allaqachon mavjud bo'lsa, mavjud yozuvni olamiz
        fetch_stmt = select(CommentLog).where(
            CommentLog.tenant_id == tenant_id,
            CommentLog.ig_comment_id == ig_comment_id
        )
        existing = await self.session.execute(fetch_stmt)
        return existing.scalars().one()

    async def queue_private_reply(
        self,
        tenant_id: uuid.UUID,
        comment_id: uuid.UUID,
        reply_text: str
    ) -> bool:
        """
        Izohga Private Reply yuborishni navbatga qo'yish ('pending').
        Faqat hozirgi holati 'none' bo'lsa navbatga qo'yiladi (Dublikat reply oldini olish).
        """
        stmt = (
            update(CommentLog)
            .where(
                CommentLog.tenant_id == tenant_id,
                CommentLog.id == comment_id,
                CommentLog.private_reply_status == "none"
            )
            .values(
                private_reply_status="pending",
                private_reply_text=reply_text
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def claim_for_sending(
        self,
        tenant_id: uuid.UUID,
        comment_id: uuid.UUID,
        worker_id: str
    ) -> Optional[CommentLog]:
        """
        Atomik tarzda izohni sending holatiga o'tkazish va lock olish.
        Lease version increment qilinadi va stale locklar tiklanadi.
        """
        sql = text("""
            UPDATE comment_logs
            SET private_reply_status = 'sending',
                private_reply_locked_at = CURRENT_TIMESTAMP,
                private_reply_locked_by = :worker_id,
                private_reply_lease_version = private_reply_lease_version + 1
            WHERE tenant_id = :tenant_id
              AND id = :comment_id
              AND (
                  private_reply_status = 'pending'
                  OR private_reply_status = 'failed_retryable'
                  OR (private_reply_status = 'sending' AND private_reply_locked_at < CURRENT_TIMESTAMP - INTERVAL '3 minutes')
              )
            RETURNING *;
        """)
        res = await self.session.execute(
            sql,
            {
                "tenant_id": tenant_id,
                "comment_id": comment_id,
                "worker_id": worker_id
            }
        )
        row = res.fetchone()
        if not row:
            return None
        # Yangilangan obyektni olish
        stmt = select(CommentLog).where(CommentLog.tenant_id == tenant_id, CommentLog.id == comment_id)
        return (await self.session.execute(stmt)).scalars().first()

    async def mark_sent(
        self,
        tenant_id: uuid.UUID,
        comment_id: uuid.UUID,
        worker_id: str,
        lease_version: int,
        reply_text: Optional[str] = None
    ) -> bool:
        """Private Reply muvaffaqiyatli yetkazildi"""
        values = {
            "private_reply_status": "sent",
            "private_reply_sent_at": datetime.now(timezone.utc),
            "private_reply_locked_at": None,
            "private_reply_locked_by": None,
            "private_reply_error": None
        }
        if reply_text:
            values["private_reply_text"] = reply_text

        stmt = (
            update(CommentLog)
            .where(
                CommentLog.tenant_id == tenant_id,
                CommentLog.id == comment_id,
                CommentLog.private_reply_locked_by == worker_id,
                CommentLog.private_reply_lease_version == lease_version
            )
            .values(**values)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def mark_failed(
        self,
        tenant_id: uuid.UUID,
        comment_id: uuid.UUID,
        worker_id: str,
        lease_version: int,
        error_message: str,
        is_permanent: bool = False
    ) -> bool:
        """Xatolik yuz berganda statusni failed_permanent yoki failed_retryable ga o'tkazish"""
        new_status = "failed_permanent" if is_permanent else "failed_retryable"
        stmt = (
            update(CommentLog)
            .where(
                CommentLog.tenant_id == tenant_id,
                CommentLog.id == comment_id,
                CommentLog.private_reply_locked_by == worker_id,
                CommentLog.private_reply_lease_version == lease_version
            )
            .values(
                private_reply_status=new_status,
                private_reply_error=error_message,
                private_reply_locked_at=None,
                private_reply_locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def mark_unknown(
        self,
        tenant_id: uuid.UUID,
        comment_id: uuid.UUID,
        worker_id: str,
        lease_version: int,
        error_message: str
    ) -> bool:
        """Tarmoq noaniqligi holati (Unknown)"""
        stmt = (
            update(CommentLog)
            .where(
                CommentLog.tenant_id == tenant_id,
                CommentLog.id == comment_id,
                CommentLog.private_reply_locked_by == worker_id,
                CommentLog.private_reply_lease_version == lease_version
            )
            .values(
                private_reply_status="unknown",
                private_reply_error=error_message,
                private_reply_locked_at=None,
                private_reply_locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0
