import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models.flow import FlowDefinition, FlowVersion
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.outbox_repo import OutboxRepository
from app.services.trigger_matcher import TriggerMatcher


class MessagingService:
    """
    Instagram Direct xabarlarini qabul qilish va avtomatlashtirish xizmati:
    - 24 soatlik Meta messaging window ni ochish va uzaytirish
    - Human takeover (operator suhbati) holatida avtomatlashtirishni to'xtatish
    - Kalit so'z va oqimlarni (flow) moslashtirish
    - Javob xabarlarini Transactional Outbox ga yozish
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def process_inbound_message(
        self,
        tenant_id: uuid.UUID,
        instagram_account: InstagramAccount,
        sender_id: str,
        message_text: Optional[str] = None,
        mid: Optional[str] = None,
        media_url: Optional[str] = None,
        media_type: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Inbound Direct xabarni to'liq qayta ishlash.
        """
        # Agar xabar akkauntning o'zidan bo'lsa (Echo), uni bot javobi deb qabul qilmaymiz
        if sender_id == instagram_account.ig_user_id:
            logger.info("Biznes akkauntning o'zidan yuborilgan echo xabar o'tkazib yuborildi", mid=mid)
            return {"status": "echo_ignored"}

        conv_repo = ConversationRepository(self.session, tenant_id=tenant_id)
        msg_repo = MessageRepository(self.session, tenant_id=tenant_id)
        outbox_repo = OutboxRepository(self.session, tenant_id=tenant_id)

        # 1. Suhbatni (Conversation) olish yoki 24h oynani ochib yangi yaratish
        conversation = await conv_repo.get_or_create(
            tenant_id=tenant_id,
            instagram_account_id=instagram_account.id,
            ig_recipient_id=sender_id
        )

        # 24h oynani yangilash
        conversation = await conv_repo.update_inbound_activity(
            tenant_id=tenant_id,
            conversation_id=conversation.id
        )

        # 2. Xabarni saqlash
        saved_msg = await msg_repo.save_message(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            mid=mid,
            sender_type="contact",
            message_text=message_text,
            media_url=media_url,
            media_type=media_type,
            status="delivered",
            raw_payload=raw_payload
        )

        # 3. Agar operator (human_takeover) yoqilgan bo'lsa, avtomatlashtirish to'xtatiladi
        if conversation.mode == "human_takeover":
            logger.info(
                "Suhbatda inson operatori (human takeover) faol, bot aralashmaydi",
                tenant_id=str(tenant_id),
                conversation_id=str(conversation.id)
            )
            await self.session.commit()
            return {
                "status": "human_takeover_active",
                "conversation_id": str(conversation.id),
                "message_id": str(saved_msg.id)
            }

        # 4. Triggerlarni tekshirish (keyword_dm)
        matching_flow = await self._find_matching_dm_flow(
            tenant_id=tenant_id,
            account_id=instagram_account.id,
            message_text=message_text or ""
        )

        reply_action = None
        if matching_flow:
            flow_def, flow_version = matching_flow
            reply_text = self._extract_reply_text(flow_version.nodes)

            if reply_text:
                # Outbox ga xavfsiz navbatga qo'yish
                dedup_key = f"dm_reply:{tenant_id}:{conversation.id}:{mid or saved_msg.id}"
                outbox_event = await outbox_repo.enqueue(
                    tenant_id=tenant_id,
                    destination="meta_api",
                    event_type="direct_message",
                    idempotency_key=dedup_key,
                    payload={
                        "instagram_account_id": str(instagram_account.id),
                        "recipient_id": sender_id,
                        "text": reply_text,
                        "conversation_id": str(conversation.id),
                        "reply_to_mid": mid
                    }
                )
                reply_action = "enqueued" if outbox_event else "deduplicated"

        await self.session.commit()
        return {
            "status": "success",
            "conversation_id": str(conversation.id),
            "message_id": str(saved_msg.id),
            "reply_action": reply_action
        }

    async def _find_matching_dm_flow(
        self,
        tenant_id: uuid.UUID,
        account_id: uuid.UUID,
        message_text: str
    ) -> Optional[tuple[FlowDefinition, FlowVersion]]:
        """Direct xabar uchun mos keluvchi faol oqimni topish"""
        stmt = (
            select(FlowDefinition, FlowVersion)
            .join(FlowVersion, FlowDefinition.active_version_id == FlowVersion.id)
            .where(
                FlowDefinition.tenant_id == tenant_id,
                FlowDefinition.instagram_account_id == account_id,
                FlowDefinition.is_active.is_(True),
                FlowVersion.is_published.is_(True),
                FlowVersion.trigger_type.in_(["keyword_dm", "dm_all"])
            )
        )
        res = await self.session.execute(stmt)
        flows = res.all()

        for flow_def, flow_version in flows:
            trigger_config = flow_version.trigger_config or {}
            if flow_version.trigger_type == "dm_all" or TriggerMatcher.match(message_text, trigger_config):
                return flow_def, flow_version

        return None

    def _extract_reply_text(self, nodes: list) -> Optional[str]:
        """Flow nodelari ichidan yuborilishi kerak bo'lgan xabar matnini olish"""
        for node in nodes:
            if node.get("type") in ("send_message", "message"):
                data = node.get("data", {})
                text = data.get("text") or data.get("message")
                if text:
                    return text
        return None
