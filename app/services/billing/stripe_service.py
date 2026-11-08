import uuid
import hmac
import hashlib
import time
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


class StripeService:
    """
    Stripe to'lov tizimi integratsiyasi:
    - Webhook imzosini tekshirish (Stripe-Signature HMAC SHA-256)
    - checkout.session.completed va invoice.payment_succeeded hodisalarini qayta ishlash
    - Obunani uzaytirish va to'lov tranzaksiyasini yozish
    """

    def __init__(self, session: AsyncSession, webhook_secret: str = "whsec_stripe_test_secret"):
        self.session = session
        self.webhook_secret = webhook_secret

    def verify_webhook_signature(self, payload: bytes, sig_header: str, tolerance: int = 300) -> bool:
        """Stripe-Signature sarlavhasini tekshirish (t=timestamp,v1=signature)"""
        if not sig_header:
            return False

        header_parts = dict(item.strip().split("=", 1) for item in sig_header.split(",") if "=" in item)
        timestamp = header_parts.get("t")
        v1_sig = header_parts.get("v1")

        if not timestamp or not v1_sig:
            return False

        # Toleransiya tekshiruvi (replay attack oldini olish)
        current_time = int(time.time())
        if abs(current_time - int(timestamp)) > tolerance:
            return False

        signed_payload = f"{timestamp}.".encode("utf-8") + payload
        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_sig, v1_sig)

    async def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stripe webhook hodisasini qayta ishlash"""
        event_type = event_data.get("type")
        data_object = event_data.get("data", {}).get("object", {})

        if event_type in ("checkout.session.completed", "invoice.payment_succeeded"):
            metadata = data_object.get("metadata", {})
            tenant_id_str = metadata.get("tenant_id")
            sub_id_str = metadata.get("subscription_id")

            if not tenant_id_str or not sub_id_str:
                logger.warning("Stripe hodisasida tenant_id yoki subscription_id topilmadi", event_id=event_data.get("id"))
                return {"status": "ignored", "reason": "Missing metadata"}

            tenant_id = uuid.UUID(tenant_id_str)
            sub_id = uuid.UUID(sub_id_str)
            amount = data_object.get("amount_total") or data_object.get("amount_paid", 0)
            currency = data_object.get("currency", "usd").upper()
            stripe_id = str(data_object.get("id"))

            payment_repo = PaymentRepository(self.session, tenant_id=tenant_id)
            sub_repo = SubscriptionRepository(self.session, tenant_id=tenant_id)

            # To'lov yozuvi
            tx = await payment_repo.create_transaction(
                tenant_id=tenant_id,
                subscription_id=sub_id,
                provider="stripe",
                provider_transaction_id=stripe_id,
                amount_minor_units=amount,
                currency=currency,
                idempotency_key=f"stripe:{stripe_id}",
                raw_callback_payload=event_data
            )
            await payment_repo.update_status(tx.id, "paid", raw_callback_payload=event_data)

            # Obunani uzaytirish
            await sub_repo.extend_subscription(tenant_id, sub_id, days_to_add=30)
            await self.session.commit()

            return {"status": "success", "transaction_id": str(tx.id)}

        return {"status": "unhandled_event", "type": event_type}
