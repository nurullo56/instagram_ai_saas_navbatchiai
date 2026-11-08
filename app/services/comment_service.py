import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models.flow import FlowDefinition, FlowVersion
from app.models.instagram import InstagramAccount
from app.models.comment import CommentLog
from app.repositories.comment_repo import CommentRepository
from app.repositories.outbox_repo import OutboxRepository
from app.services.trigger_matcher import TriggerMatcher


class CommentService:
    """
    Instagram izohlarini qayta ishlash xizmati:
    - 7 kunlik Meta cheklovini tekshirish (asl ig_comment_created_at bo'yicha)
    - Trigger va kalit so'zlarni moslashtirish (TriggerMatcher)
    - Private Reply va Public Reply larni Transactional Outbox ga xavfsiz navbatlash
    - 5-holatli mashina va atomik dublikat himoyasi
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_comment_event(
        self,
        tenant_id: uuid.UUID,
        instagram_account: InstagramAccount,
        ig_comment_id: str,
        ig_media_id: str,
        ig_user_id: str,
        comment_text: str,
        ig_comment_created_at: datetime
    ) -> Dict[str, Any]:
        """
        Inbound izoh eventini to'liq qayta ishlash.
        """
        comment_repo = CommentRepository(self.session, tenant_id=tenant_id)
        outbox_repo = OutboxRepository(self.session, tenant_id=tenant_id)

        # 1. Izohni bazaga kiritish yoki mavjudini olish
        comment = await comment_repo.upsert_comment(
            tenant_id=tenant_id,
            instagram_account_id=instagram_account.id,
            ig_comment_id=ig_comment_id,
            ig_media_id=ig_media_id,
            ig_user_id=ig_user_id,
            comment_text=comment_text,
            ig_comment_created_at=ig_comment_created_at
        )

        # 2. Meta 7 kunlik qat'iy cheklovini tekshirish (Architecture v2.5 talabi)
        now = datetime.now(timezone.utc)
        if ig_comment_created_at.tzinfo is None:
            ig_comment_created_at = ig_comment_created_at.replace(tzinfo=timezone.utc)

        is_expired_7d = (now - ig_comment_created_at) > timedelta(days=7)
        if is_expired_7d:
            logger.warning(
                "Instagram izohi 7 kundan eski, Private Reply yuborish taqiqlanadi",
                tenant_id=str(tenant_id),
                ig_comment_id=ig_comment_id,
                ig_comment_created_at=ig_comment_created_at.isoformat()
            )
            return {
                "status": "skipped_expired_7d",
                "comment_id": str(comment.id),
                "reason": "Comment is older than 7 days"
            }

        # 3. Agar Private Reply allaqachon yuborilgan yoki yuborilmoqda bo'lsa - to'xtatish
        if comment.private_reply_status in ("sent", "sending", "pending", "failed_permanent"):
            logger.info(
                "Izohga Private Reply allaqachon belgilangan, qayta yuborilmaydi",
                tenant_id=str(tenant_id),
                comment_id=str(comment.id),
                status=comment.private_reply_status
            )
            return {
                "status": "already_processed",
                "comment_id": str(comment.id),
                "private_reply_status": comment.private_reply_status
            }

        # 4. Mos keluvchi faol trigger/flow larni qidirish
        matching_flow = await self._find_matching_comment_flow(
            tenant_id=tenant_id,
            account_id=instagram_account.id,
            comment_text=comment_text
        )

        if not matching_flow:
            logger.info(
                "Izoh uchun mos keluvchi avtomatizatsiya topilmadi",
                tenant_id=str(tenant_id),
                ig_comment_id=ig_comment_id,
                text=comment_text
            )
            return {"status": "no_trigger_matched", "comment_id": str(comment.id)}

        flow_def, flow_version = matching_flow

        # Flow nodelaridan javoblarni ajratib olish
        private_reply_text = None
        public_reply_text = None

        for node in flow_version.nodes:
            data = node.get("data", {})
            node_type = node.get("type")
            if node_type == "comment_reply":
                private_reply_text = data.get("private_reply_text")
                public_reply_text = data.get("public_reply_text")
            elif node_type == "send_message" and not private_reply_text:
                private_reply_text = data.get("text")

        results = {}

        # 5. Private Reply ni navbatga qo'yish
        if private_reply_text:
            queued = await comment_repo.queue_private_reply(
                tenant_id=tenant_id,
                comment_id=comment.id,
                reply_text=private_reply_text
            )
            if queued:
                outbox_event = await outbox_repo.enqueue(
                    tenant_id=tenant_id,
                    destination="meta_api",
                    event_type="comment_private_reply",
                    idempotency_key=f"comment_private_reply:{tenant_id}:{ig_comment_id}",
                    payload={
                        "instagram_account_id": str(instagram_account.id),
                        "comment_id": ig_comment_id,
                        "text": private_reply_text,
                        "comment_log_id": str(comment.id),
                        "recipient_user_id": ig_user_id
                    }
                )
                results["private_reply"] = "enqueued" if outbox_event else "deduplicated"

        # 6. Public Reply ni navbatga qo'yish (agar sozlangan bo'lsa)
        if public_reply_text:
            outbox_pub = await outbox_repo.enqueue(
                tenant_id=tenant_id,
                destination="meta_api",
                event_type="comment_public_reply",
                idempotency_key=f"comment_public_reply:{tenant_id}:{ig_comment_id}",
                payload={
                    "instagram_account_id": str(instagram_account.id),
                    "comment_id": ig_comment_id,
                    "text": public_reply_text,
                    "comment_log_id": str(comment.id)
                }
            )
            results["public_reply"] = "enqueued" if outbox_pub else "deduplicated"

        await self.session.commit()
        return {
            "status": "success",
            "comment_id": str(comment.id),
            "flow_id": str(flow_def.id),
            "actions": results
        }

    async def _find_matching_comment_flow(
        self,
        tenant_id: uuid.UUID,
        account_id: uuid.UUID,
        comment_text: str
    ) -> Optional[tuple[FlowDefinition, FlowVersion]]:
        """
        Izoh matniga mos keladigan faol va e'lon qilingan oqimni (flow) topish.
        """
        stmt = (
            select(FlowDefinition, FlowVersion)
            .join(FlowVersion, FlowDefinition.active_version_id == FlowVersion.id)
            .where(
                FlowDefinition.tenant_id == tenant_id,
                FlowDefinition.instagram_account_id == account_id,
                FlowDefinition.is_active.is_(True),
                FlowVersion.is_published.is_(True),
                FlowVersion.trigger_type.in_(["comment_keyword", "comment_all"])
            )
        )
        res = await self.session.execute(stmt)
        flows = res.all()

        for flow_def, flow_version in flows:
            trigger_config = flow_version.trigger_config or {}
            if flow_version.trigger_type == "comment_all" or TriggerMatcher.match(comment_text, trigger_config):
                return flow_def, flow_version

        return None
