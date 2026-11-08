import json
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.config.logging import logger
from app.integrations.meta.webhooks import verify_meta_webhook_signature
from app.services.webhook_normalizer import normalize_meta_webhook_payload
from app.repositories.webhook_repo import WebhookRepository


class WebhookService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = WebhookRepository(session)

    def verify_webhook_challenge(
        self,
        hub_mode: Optional[str],
        hub_verify_token: Optional[str],
        hub_challenge: Optional[str]
    ) -> str:
        """
        Meta Webhook verification (GET endpoint).
        Meta serverlari hub.mode='subscribe' va bizning verify_tokenimizni tekshirish uchun yuboradi.
        """
        if hub_mode == "subscribe" and hub_verify_token == settings.META_WEBHOOK_VERIFY_TOKEN:
            logger.info("Meta Webhook verifikatsiyasi muvaffaqiyatli o'tdi")
            return hub_challenge or ""
        logger.warning(
            "Meta Webhook verifikatsiyasi rad etildi",
            hub_mode=hub_mode,
            hub_verify_token=hub_verify_token
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Webhook verify_token mos kelmadi"
        )

    async def ingest_webhook_events(
        self,
        raw_payload_bytes: bytes,
        signature_header: Optional[str]
    ) -> Dict[str, Any]:
        """
        Meta Webhook eventlarini qabul qilish (POST endpoint):
        1. HMAC SHA-256 imzo tekshiruvi.
        2. Multi-event batch payloadni ajratish va deterministik ID berish.
        3. Webhook inbox bazasiga tranzaksion va idempotent kiritish.
        """
        # 1. Imzo tekshiruvi
        if not signature_header or not verify_meta_webhook_signature(raw_payload_bytes, signature_header):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="X-Hub-Signature-256 imzosi yaroqsiz"
            )

        # 2. JSON parse
        try:
            payload_dict = json.loads(raw_payload_bytes.decode("utf-8"))
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Noto'g'ri JSON formati")

        # 3. Normallashtirish
        normalized_events = normalize_meta_webhook_payload(payload_dict)
        if not normalized_events:
            logger.info("Payload ichida qayta ishlanadigan hodisalar topilmadi")
            return {"status": "ok", "events_count": 0}

        # 4. Idempotent saqlash
        inserted_ids = await self.repo.insert_events_idempotent(normalized_events)
        await self.session.commit()

        logger.info(
            "Webhook hodisalari qabul qilindi va saqlandi",
            total_events=len(normalized_events),
            new_events=len(inserted_ids)
        )

        return {
            "status": "ok",
            "received": len(normalized_events),
            "stored": len(inserted_ids)
        }
