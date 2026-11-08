import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select
from app.config.logging import logger
from app.database.session import async_session_factory
from app.models.instagram import InstagramAccount
from app.repositories.webhook_repo import WebhookRepository
from app.services.comment_service import CommentService
from app.services.messaging_service import MessagingService
from app.services.outbound_dispatcher import OutboundDispatcher


async def task_process_webhook_batch(ctx: Optional[Dict[str, Any]] = None, worker_id: str = "worker-1") -> int:
    """
    ARQ fon vazifasi: navbatdagi webhook hodisalarini egallab (claim with fencing token) qayta ishlash.
    Hodisa turiga qarab CommentService yoki MessagingService ga yo'naltiriladi.
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
            event_payload = ev[3]

            try:
                # 1. Akkauntni aniqlash
                account_external_id = event_payload.get("account_id")
                payload_data = event_payload.get("payload", {})

                # Instagram akkauntini topish
                stmt = select(InstagramAccount).where(
                    (InstagramAccount.ig_user_id == account_external_id) |
                    (InstagramAccount.page_id == account_external_id)
                )
                account_res = await session.execute(stmt)
                account = account_res.scalars().first()

                if account:
                    tenant_id = account.tenant_id

                    # A. Direct xabarni qayta ishlash
                    if "message" in payload_data and "sender" in payload_data:
                        sender_id = str(payload_data.get("sender", {}).get("id"))
                        msg_info = payload_data.get("message", {})
                        msg_text = msg_info.get("text")
                        mid = msg_info.get("mid")

                        msg_service = MessagingService(session)
                        await msg_service.process_inbound_message(
                            tenant_id=tenant_id,
                            instagram_account=account,
                            sender_id=sender_id,
                            message_text=msg_text,
                            mid=mid,
                            raw_payload=payload_data
                        )

                    # B. Izohni qayta ishlash (changes -> field: comments)
                    elif payload_data.get("field") == "comments":
                        val = payload_data.get("value", {})
                        comment_id = str(val.get("id"))
                        media_id = str(val.get("media", {}).get("id") or val.get("post_id", "unknown"))
                        user_id = str(val.get("from", {}).get("id", "unknown"))
                        comment_text = val.get("text", "")
                        created_time_unix = val.get("created_time")

                        if created_time_unix:
                            comment_created_at = datetime.fromtimestamp(created_time_unix, tz=timezone.utc)
                        else:
                            comment_created_at = datetime.now(timezone.utc)

                        comment_service = CommentService(session)
                        await comment_service.process_comment_event(
                            tenant_id=tenant_id,
                            instagram_account=account,
                            ig_comment_id=comment_id,
                            ig_media_id=media_id,
                            ig_user_id=user_id,
                            comment_text=comment_text,
                            ig_comment_created_at=comment_created_at
                        )

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


async def task_dispatch_outbox_batch(ctx: Optional[Dict[str, Any]] = None, worker_id: str = "dispatcher-1") -> int:
    """
    ARQ fon vazifasi: Transactional Outbox dagi pending xabarlarni egallab jo'natish.
    """
    async with async_session_factory() as session:
        dispatcher = OutboundDispatcher(session)
        dispatched_count = await dispatcher.dispatch_batch(worker_id=worker_id, limit=10)
        return dispatched_count


async def task_sweep_stale_webhooks(ctx: Optional[Dict[str, Any]] = None) -> int:
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
