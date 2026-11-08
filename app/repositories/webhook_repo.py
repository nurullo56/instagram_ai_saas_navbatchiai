import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import WebhookEvent


class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def insert_events_idempotent(self, events: List[Dict[str, Any]]) -> List[str]:
        """
        Normallashtirilgan webhook eventlarni tranzaksion va idempotent kiritish.
        ON CONFLICT (source, event_id) DO NOTHING orqali takroriy hodisalar o'tkazib yuboriladi.
        """
        if not events:
            return []

        inserted_event_ids = []
        for ev in events:
            stmt = insert(WebhookEvent).values(
                source=ev.get("source", "meta"),
                event_id=ev["event_id"],
                payload=ev["payload"],
                status="received",
                retry_count=0,
                max_retries=5,
                lease_version=1,
            ).on_conflict_do_nothing(index_elements=["source", "event_id"]).returning(WebhookEvent.event_id)

            res = await self.session.execute(stmt)
            row = res.scalars().first()
            if row:
                inserted_event_ids.append(row)

        await self.session.flush()
        return inserted_event_ids

    async def claim_events_for_processing(self, worker_id: str, limit: int = 10) -> List[WebhookEvent]:
        """
        Worker uchun hodisalarni bloklab olish (Stale recovery, Lease Fencing va SKIP LOCKED bilan).
        """
        claim_sql = text("""
            WITH claimable AS (
                SELECT id, lease_version, status, retry_count
                FROM webhook_events
                WHERE (
                    (status = 'received' AND next_retry_at <= CURRENT_TIMESTAMP)
                    OR (status = 'failed' AND retry_count < max_retries AND next_retry_at <= CURRENT_TIMESTAMP)
                    OR (status = 'processing' AND retry_count < max_retries AND (locked_at IS NULL OR locked_at < CURRENT_TIMESTAMP - INTERVAL '3 minutes'))
                )
                ORDER BY received_at ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            )
            UPDATE webhook_events
            SET status = 'processing',
                locked_at = CURRENT_TIMESTAMP,
                locked_by = :worker_id,
                lease_version = webhook_events.lease_version + 1,
                retry_count = CASE 
                    WHEN claimable.status IN ('processing', 'failed') THEN webhook_events.retry_count + 1 
                    ELSE webhook_events.retry_count 
                END
            FROM claimable
            WHERE webhook_events.id = claimable.id
            RETURNING webhook_events.id, webhook_events.source, webhook_events.event_id, 
                      webhook_events.payload, webhook_events.lease_version, webhook_events.retry_count;
        """)

        res = await self.session.execute(claim_sql, {"worker_id": worker_id, "limit": limit})
        return list(res.fetchall())

    async def mark_processed(self, id: uuid.UUID, lease_version: int, worker_id: str) -> bool:
        """Fencing tekshiruvi bilan muvaffaqiyatli yakunlash"""
        stmt = (
            update(WebhookEvent)
            .where(
                WebhookEvent.id == id,
                WebhookEvent.lease_version == lease_version,
                WebhookEvent.locked_by == worker_id
            )
            .values(
                status="processed",
                processed_at=datetime.now(timezone.utc),
                locked_at=None,
                locked_by=None
            )
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def mark_failed(self, id: uuid.UUID, lease_version: int, worker_id: str, error_message: str, max_retries: int = 5) -> bool:
        """Xatolik bilan yakunlash (oxirgi urinishda avtomatik DLQ ga o'tish)"""
        fail_sql = text("""
            UPDATE webhook_events
            SET status = CASE WHEN retry_count >= max_retries THEN 'dlq' ELSE 'failed' END,
                next_retry_at = CURRENT_TIMESTAMP + (POWER(2, LEAST(retry_count, 6)) * INTERVAL '10 seconds'),
                locked_at = NULL,
                locked_by = NULL,
                error_message = :err_msg
            WHERE id = :id AND lease_version = :lease_version AND locked_by = :worker_id;
        """)
        res = await self.session.execute(fail_sql, {
            "id": id,
            "lease_version": lease_version,
            "worker_id": worker_id,
            "err_msg": error_message
        })
        return res.rowcount > 0

    async def sweep_stale_to_dlq(self) -> int:
        """Qulab max_retries dan oshgan yoki failed bo'lib muddati tugaganlarni DLQ ga o'tkazish"""
        sweep_sql = text("""
            UPDATE webhook_events
            SET status = 'dlq',
                locked_at = NULL,
                locked_by = NULL,
                error_message = 'Max retries exceeded: moved to DLQ by sweeper'
            WHERE (
                (status = 'processing' AND retry_count >= max_retries AND (locked_at IS NULL OR locked_at < CURRENT_TIMESTAMP - INTERVAL '3 minutes'))
                OR (status = 'failed' AND retry_count >= max_retries)
            );
        """)
        res = await self.session.execute(sweep_sql)
        return res.rowcount
