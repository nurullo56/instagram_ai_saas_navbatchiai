import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outbox import OutboxEvent
from app.repositories.base import BaseRepository


class OutboxRepository(BaseRepository[OutboxEvent]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(OutboxEvent, session, tenant_id=tenant_id)

    async def enqueue(
        self,
        tenant_id: uuid.UUID,
        destination: str,
        event_type: str,
        idempotency_key: str,
        payload: Dict[str, Any]
    ) -> Optional[OutboxEvent]:
        """
        Chiquvchi xabarni Transactional Outbox navbatiga yozish.
        ON CONFLICT DO NOTHING sababli bitta idempotency_key bilan ikkinchi nusxa yozilmaydi.
        """
        stmt = (
            insert(OutboxEvent)
            .values(
                tenant_id=tenant_id,
                destination=destination,
                event_type=event_type,
                idempotency_key=idempotency_key,
                payload=payload,
                status="pending",
                retry_count=0,
                max_retries=5,
            )
            .on_conflict_do_nothing(index_elements=["tenant_id", "idempotency_key"])
            .returning(OutboxEvent)
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def claim_pending_events(self, worker_id: str, limit: int = 10) -> List[OutboxEvent]:
        """
        Outbox navbatidagi jo'natishga tayyor xabarlarni egallash (FOR UPDATE SKIP LOCKED).
        """
        claim_sql = text("""
            WITH claimable AS (
                SELECT id
                FROM outbox_events
                WHERE (
                    (status = 'pending' AND next_retry_at <= CURRENT_TIMESTAMP)
                    OR (status = 'rejected_transient' AND retry_count < max_retries AND next_retry_at <= CURRENT_TIMESTAMP)
                    OR (status = 'sending' AND locked_at < CURRENT_TIMESTAMP - INTERVAL '3 minutes')
                )
                ORDER BY created_at ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            )
            UPDATE outbox_events
            SET status = 'sending',
                locked_at = CURRENT_TIMESTAMP,
                locked_by = :worker_id
            FROM claimable
            WHERE outbox_events.id = claimable.id
            RETURNING outbox_events.*;
        """)
        res = await self.session.execute(claim_sql, {"worker_id": worker_id, "limit": limit})
        return list(res.fetchall())

    async def mark_accepted_by_meta(self, id: uuid.UUID, worker_id: str) -> bool:
        """Meta xabarni qabul qildi (accepted_by_meta)"""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == id, OutboxEvent.locked_by == worker_id)
            .values(
                status="accepted_by_meta",
                sent_at=datetime.now(timezone.utc),
                locked_at=None,
                locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def mark_rejected_transient(self, id: uuid.UUID, worker_id: str, error_message: str) -> bool:
        """Vaqtinchalik xatolik (Rate limit / 5xx) - exponential backoff bilan qayta urinish"""
        sql = text("""
            UPDATE outbox_events
            SET retry_count = retry_count + 1,
                status = CASE WHEN retry_count + 1 >= max_retries THEN 'rejected_permanent' ELSE 'rejected_transient' END,
                next_retry_at = CURRENT_TIMESTAMP + (POWER(2, LEAST(retry_count + 1, 6)) * INTERVAL '10 seconds'),
                locked_at = NULL,
                locked_by = NULL,
                error_message = :err_msg
            WHERE id = :id AND locked_by = :worker_id;
        """)
        res = await self.session.execute(sql, {"id": id, "worker_id": worker_id, "err_msg": error_message})
        return res.rowcount > 0

    async def mark_rejected_permanent(self, id: uuid.UUID, worker_id: str, error_message: str) -> bool:
        """Doimiy xatolik (24h oyna, noto'g'ri parametr) - qayta urinish yo'q"""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == id, OutboxEvent.locked_by == worker_id)
            .values(
                status="rejected_permanent",
                error_message=error_message,
                locked_at=None,
                locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def mark_unknown(self, id: uuid.UUID, worker_id: str, error_message: str) -> bool:
        """Tarmoq timeouti - reconciliation kutiladi"""
        stmt = (
            update(OutboxEvent)
            .where(OutboxEvent.id == id, OutboxEvent.locked_by == worker_id)
            .values(
                status="unknown",
                error_message=error_message,
                locked_at=None,
                locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0
