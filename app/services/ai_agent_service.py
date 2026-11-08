import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation
from app.repositories.ai_repo import AIRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.lead_repo import LeadRepository
from app.repositories.outbox_repo import OutboxRepository
from app.integrations.openrouter.client import OpenRouterClient
from app.services.lead_extractor import LeadExtractor


class AIAgentService:
    """
    AI Yordamchi (Agent) xizmati:
    - Inson operatoriga uzatish (Live Agent Handoff)
    - Kontekst va RAG bilimlar bazasini promptga joylash
    - OpenRouter orqali javob generatsiya qilish
    - Suhbatdan avtomatik Lead (telefon, email, ism) yig'ish
    - Javobni Transactional Outbox ga xavfsiz navbatlash
    """

    HANDOFF_KEYWORDS = [
        "operator", "inson", "menejer", "manager", "admin", "administrator",
        "odam", "jonli muloqot", "operatorga ula", "mutaxassis"
    ]

    def __init__(
        self,
        session: AsyncSession,
        openrouter_client: Optional[OpenRouterClient] = None
    ):
        self.session = session
        self.client = openrouter_client or OpenRouterClient()

    def check_handoff_intent(self, text: str) -> bool:
        """Mijoz inson operatorini talab qilayotganini tekshirish"""
        normalized = (text or "").lower()
        return any(kw in normalized for kw in self.HANDOFF_KEYWORDS)

    async def process_ai_interaction(
        self,
        tenant_id: uuid.UUID,
        instagram_account: InstagramAccount,
        conversation: Conversation,
        user_message_text: str
    ) -> Dict[str, Any]:
        """
        AI agent bilan o'zaro aloqani amalga oshirish.
        """
        conv_repo = ConversationRepository(self.session, tenant_id=tenant_id)
        outbox_repo = OutboxRepository(self.session, tenant_id=tenant_id)
        ai_repo = AIRepository(self.session, tenant_id=tenant_id)
        msg_repo = MessageRepository(self.session, tenant_id=tenant_id)
        lead_repo = LeadRepository(self.session, tenant_id=tenant_id)

        # 1. Inson operatoriga uzatish (Handoff) tekshiruvi
        if self.check_handoff_intent(user_message_text):
            logger.info(
                "Mijoz inson operatorini talab qildi, suhbat rejimi human_takeover ga o'tkazildi",
                conversation_id=str(conversation.id)
            )
            await conv_repo.set_mode(tenant_id, conversation.id, "human_takeover")

            handoff_msg = "Siz inson operatoriga ulandingiz. Mutaxassisimiz tez orada javob beradi! 👨‍💼"
            await outbox_repo.enqueue(
                tenant_id=tenant_id,
                destination="meta_api",
                event_type="direct_message",
                idempotency_key=f"handoff:{tenant_id}:{conversation.id}:{uuid.uuid4()}",
                payload={
                    "instagram_account_id": str(instagram_account.id),
                    "recipient_id": conversation.ig_recipient_id,
                    "text": handoff_msg,
                    "conversation_id": str(conversation.id)
                }
            )
            await self.session.commit()
            return {"status": "handoff_triggered", "conversation_mode": "human_takeover"}

        # 2. Akkauntning AI konfiguratsiyasini tekshirish
        ai_config = await ai_repo.get_config_by_account(tenant_id, instagram_account.id)
        if not ai_config or not ai_config.is_active:
            logger.info("Akkauntda AI agent faol emas yoki sozlanmagan", account_id=str(instagram_account.id))
            return {"status": "ai_disabled"}

        # 3. Lead ma'lumotlarini ajratib olish (Lead Capture)
        if ai_config.lead_capture_enabled:
            extracted = LeadExtractor.extract_all(user_message_text)
            if any(extracted.values()):
                logger.info(
                    "Suhbatdan yangi lead ma'lumotlari aniqlandi",
                    conversation_id=str(conversation.id),
                    extracted=extracted
                )
                await lead_repo.upsert_lead(
                    tenant_id=tenant_id,
                    instagram_account_id=instagram_account.id,
                    ig_recipient_id=conversation.ig_recipient_id,
                    username=conversation.recipient_username,
                    full_name=extracted.get("full_name"),
                    phone_number=extracted.get("phone_number"),
                    email=extracted.get("email")
                )

        # 4. Suhbat tarixini olish (oxirgi 6 ta xabar)
        history_records = await msg_repo.get_messages_by_conversation(tenant_id, conversation.id, limit=6)
        messages_payload: List[Dict[str, str]] = []

        system_instruction = (
            f"{ai_config.system_prompt}\n\n"
            "QOIDALAR:\n"
            "- Qisqa, tushunarli va do'stona muloqot qil (Instagram Direct formati).\n"
            "- Mavzudan tashqari savollarga xushmuomala bilan biznes xizmatlariga qaytar.\n"
            "- Agar mijoz inson bilan bog'lanishni xohlasa, 'operator' so'zini eslat.\n"
        )
        messages_payload.append({"role": "system", "content": system_instruction})

        for msg in history_records:
            if msg.sender_type in ("contact", "user"):
                messages_payload.append({"role": "user", "content": msg.message_text or ""})
            elif msg.sender_type in ("bot", "ai"):
                messages_payload.append({"role": "assistant", "content": msg.message_text or ""})

        # Hozirgi xabar tarixda bo'lmasa, qo'shamiz
        if not messages_payload or messages_payload[-1].get("content") != user_message_text:
            messages_payload.append({"role": "user", "content": user_message_text})

        # 5. OpenRouter orqali AI javobini olish
        completion = await self.client.complete(
            messages=messages_payload,
            model=ai_config.model_name,
            temperature=float(ai_config.temperature),
            max_tokens=ai_config.max_tokens
        )
        ai_reply_text = completion.get("content", "").strip()

        if not ai_reply_text:
            return {"status": "empty_ai_response"}

        # 6. Javobni Outbox ga xavfsiz navbatlash
        await outbox_repo.enqueue(
            tenant_id=tenant_id,
            destination="meta_api",
            event_type="direct_message",
            idempotency_key=f"ai_reply:{tenant_id}:{conversation.id}:{uuid.uuid4()}",
            payload={
                "instagram_account_id": str(instagram_account.id),
                "recipient_id": conversation.ig_recipient_id,
                "text": ai_reply_text,
                "conversation_id": str(conversation.id)
            }
        )

        await self.session.commit()
        return {
            "status": "success",
            "reply_text": ai_reply_text,
            "model_used": completion.get("model")
        }
