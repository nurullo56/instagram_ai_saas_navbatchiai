import uuid
import hashlib
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


class ClickService:
    """
    Click to'lov tizimi integratsiyasi:
    - Prepare (action=0): hisob va imzoni tekshirish, pending tranzaksiya ochish
    - Complete (action=1): to'lovni tasdiqlash va obunani uzaytirish
    - MD5 imzo (sign_string) orqali xavfsizlik tekshiruvi
    """

    def __init__(self, session: AsyncSession, secret_key: str = "click_secret_key"):
        self.session = session
        self.secret_key = secret_key

    def verify_signature(
        self,
        click_trans_id: str,
        service_id: str,
        merchant_trans_id: str,
        amount: str,
        action: str,
        sign_time: str,
        sign_string: str,
        merchant_prepare_id: Optional[str] = None
    ) -> bool:
        """MD5 imzoni tekshirish"""
        prep_id_str = merchant_prepare_id or "" if action == "1" else ""
        raw_str = f"{click_trans_id}{service_id}{self.secret_key}{merchant_trans_id}{prep_id_str}{amount}{action}{sign_time}"
        expected_sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()
        return expected_sign.lower() == (sign_string or "").lower()

    async def handle_prepare(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare so'rovi (action=0)"""
        click_trans_id = str(data.get("click_trans_id"))
        service_id = str(data.get("service_id"))
        merchant_trans_id = str(data.get("merchant_trans_id"))
        amount = str(data.get("amount"))
        action = str(data.get("action"))
        sign_time = str(data.get("sign_time"))
        sign_string = str(data.get("sign_string"))

        if not self.verify_signature(click_trans_id, service_id, merchant_trans_id, amount, action, sign_time, sign_string):
            return {"error": -1, "error_note": "SIGN CHECK FAILED"}

        # merchant_trans_id da tenant_id:subscription_id beriladi
        try:
            tenant_id_str, sub_id_str = merchant_trans_id.split(":")
            tenant_id = uuid.UUID(tenant_id_str)
            sub_id = uuid.UUID(sub_id_str)
        except Exception:
            return {"error": -5, "error_note": "User not found"}

        sub_repo = SubscriptionRepository(self.session, tenant_id=tenant_id)
        sub = await sub_repo.get_by_id(sub_id)
        if not sub:
            return {"error": -5, "error_note": "Subscription not found"}

        amount_cents = int(float(amount) * 100)
        payment_repo = PaymentRepository(self.session, tenant_id=tenant_id)

        tx = await payment_repo.create_transaction(
            tenant_id=tenant_id,
            subscription_id=sub_id,
            provider="click",
            provider_transaction_id=click_trans_id,
            amount_minor_units=amount_cents,
            currency="UZS",
            idempotency_key=f"click:{click_trans_id}",
            raw_callback_payload=data
        )
        await self.session.commit()

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": str(tx.id),
            "error": 0,
            "error_note": "Success"
        }

    async def handle_complete(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete so'rovi (action=1)"""
        click_trans_id = str(data.get("click_trans_id"))
        service_id = str(data.get("service_id"))
        merchant_trans_id = str(data.get("merchant_trans_id"))
        merchant_prepare_id = str(data.get("merchant_prepare_id"))
        amount = str(data.get("amount"))
        action = str(data.get("action"))
        sign_time = str(data.get("sign_time"))
        sign_string = str(data.get("sign_string"))
        error = int(data.get("error", 0))

        if not self.verify_signature(click_trans_id, service_id, merchant_trans_id, amount, action, sign_time, sign_string, merchant_prepare_id):
            return {"error": -1, "error_note": "SIGN CHECK FAILED"}

        payment_repo = PaymentRepository(self.session)
        tx = await payment_repo.get_by_id(uuid.UUID(merchant_prepare_id))
        if not tx:
            return {"error": -6, "error_note": "Transaction not found"}

        if error < 0:
            await payment_repo.update_status(tx.id, "failed", raw_callback_payload=data)
            await self.session.commit()
            return {"error": error, "error_note": "Transaction canceled"}

        if tx.status == "paid":
            return {
                "click_trans_id": click_trans_id,
                "merchant_trans_id": merchant_trans_id,
                "merchant_confirm_id": str(tx.id),
                "error": 0,
                "error_note": "Success"
            }

        # Obunani 30 kunga uzaytirish
        sub_repo = SubscriptionRepository(self.session, tenant_id=tx.tenant_id)
        await sub_repo.extend_subscription(tx.tenant_id, tx.subscription_id, days_to_add=30)

        await payment_repo.update_status(tx.id, "paid", raw_callback_payload=data)
        await self.session.commit()

        return {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": str(tx.id),
            "error": 0,
            "error_note": "Success"
        }
