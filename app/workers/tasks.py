import uuid
from typing import Dict, Any
from app.config.logging import logger
from app.database.session import async_session_factory
from app.repositories.webhook_repo import WebhookRepository


async def task_process_webhook_batch(ctx: Dict[str, Any], worker_id: str = "worker-1"):
    """
    ARQ fon vazifasi: navbatdagi webhook hodisalarini egallab (claim with fencing token) qayta ishlash.
    """
    async with async_session_factory() as session:
        repo = WebhookRepository(session)
        events = await repo.claim_events_for_processing(worker_id=worker_id, limit=10)
        if not events:
            return 0

        logger.info("Worker hodisalarni egalladi", count=len(events), worker_id=worker_id)
        processed_count = 0

        for ev in events:
            event_id_val = ev[0]
            lease_version_val = ev[4]
            payload = ev[3]

            try:
                # Kelajakda: domen servislari (Flow engine, inbox, lead extractor) chaqiriladi
                logger.debug("Hodisa qayta ishlanmoqda", event_id=str(event_id_val))

                # Fencing token bilan muvaffaqiyatli yakunlash
                success = await repo.mark_processed(
                    id=event_id_val,
                    lease_version=lease_version_val,
                    worker_id=worker_id
                )
                if success:
                    processed_count += 1
                else:
                    logger.warning("Lease yo'qotilgani sabab natija bekor qilindi (Zombie worker himoyasi)", id=str(event_id_val))
            except Exception as e:
                logger.error("Hodisani qayta ishlashda xato", event_id=str(event_id_val), error=str(e))
                await repo.mark_failed(
                    id=event_id_val,
                    lease_version=lease_version_val,
                    worker_id=worker_id,
                    error_message=str(e)
                )

        await session.commit()
        return processed_count


async def task_sweep_stale_webhooks(ctx: Dict[str, Any]):
    """
    Periodik Sweeper vazifasi: Worker qulab (crash) limitdan oshgan yoki
    failed bo'lib muddati tugagan vazifalarni DLQ ga o'tkazish.
    """
    async with async_session_factory() as session:
        repo = WebhookRepository(session)
        count = await repo.sweep_stale_to_dlq()
        await session.commit()
        if count > 0:
            logger.info("Sweeper stale hodisalarni DLQ ga o'tkazdi", count=count)
        return count
