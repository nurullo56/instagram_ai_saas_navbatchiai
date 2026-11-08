import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


class PaymeService:
    """
    Payme JSON-RPC 2.0 to'lov protokoli implementatsiyasi:
    - CheckPerformTransaction: hisob va summani tekshirish
    - CreateTransaction: to'lov tranzaksiyasini yaratish (holat: 1)
    - PerformTransaction: to'lovni tasdiqlash va obunani uzaytirish (holat: 2)
    - CancelTransaction: bekor qilish (holat: -1 yoki -2)
    - CheckTransaction: tranzaksiya holatini tekshirish
    """

    STATE_CREATED = 1
    STATE_COMPLETED = 2
    STATE_CANCELLED = -1
    STATE_CANCELLED_AFTER_COMPLETE = -2

    def __init__(self, session: AsyncSession):
        self.session = session

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Payme JSON-RPC so'rovini yo'naltirish va javob berish"""
        method = request_data.get("method")
        params = request_data.get("params", {})
        req_id = request_data.get("id")

        try:
            if method == "CheckPerformTransaction":
                res = await self.check_perform_transaction(params)
            elif method == "CreateTransaction":
                res = await self.create_transaction(params)
            elif method == "PerformTransaction":
                res = await self.perform_transaction(params)
            elif method == "CancelTransaction":
                res = await self.cancel_transaction(params)
            elif method == "CheckTransaction":
                res = await self.check_transaction(params)
            else:
                return self._error_response(-32601, "Metod topilmadi", req_id)

            return {"result": res, "id": req_id}

        except PaymeException as e:
            return self._error_response(e.code, e.message, req_id)
        except Exception as e:
            logger.error("Payme so'rovini bajarishda kutilmagan xato", error=str(e), method=method)
            return self._error_response(-31008, f"Tizim xatoligi: {str(e)}", req_id)

    async def check_perform_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        account = params.get("account", {})
        amount = params.get("amount")

        tenant_id_str = account.get("tenant_id")
        sub_id_str = account.get("subscription_id")

        if not tenant_id_str or not sub_id_str:
            raise PaymeException(-31001, "tenant_id yoki subscription_id ko'rsatilmadi")

        tenant_id = uuid.UUID(tenant_id_str)
        sub_id = uuid.UUID(sub_id_str)

        sub_repo = SubscriptionRepository(self.session, tenant_id=tenant_id)
        sub = await sub_repo.get_by_id(sub_id)
        if not sub:
            raise PaymeException(-31001, "Obuna topilmadi")

        if not amount or amount <= 0:
            raise PaymeException(-31002, "Noto'g'ri summa")

        return {"allow": True}

    async def create_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tx_id = params.get("id")
        amount = params.get("amount")
        account = params.get("account", {})
        time = params.get("time", int(datetime.now(timezone.utc).timestamp() * 1000))

        tenant_id = uuid.UUID(account["tenant_id"])
        sub_id = uuid.UUID(account["subscription_id"])

        payment_repo = PaymentRepository(self.session, tenant_id=tenant_id)
        existing = await payment_repo.get_by_provider_tx(provider="payme", provider_transaction_id=tx_id)

        if existing:
            state = self.STATE_COMPLETED if existing.status == "paid" else self.STATE_CREATED
            return {
                "create_time": time,
                "transaction": str(existing.id),
                "state": state
            }

        # Yangi tranzaksiya ochamiz
        tx = await payment_repo.create_transaction(
            tenant_id=tenant_id,
            subscription_id=sub_id,
            provider="payme",
            provider_transaction_id=tx_id,
            amount_minor_units=amount,
            currency="UZS",
            idempotency_key=f"payme:{tx_id}",
            raw_callback_payload=params
        )
        await self.session.commit()

        return {
            "create_time": time,
            "transaction": str(tx.id),
            "state": self.STATE_CREATED
        }

    async def perform_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tx_id = params.get("id")
        payment_repo = PaymentRepository(self.session)
        tx = await payment_repo.get_by_provider_tx(provider="payme", provider_transaction_id=tx_id)

        if not tx:
            raise PaymeException(-31003, "Tranzaksiya topilmadi")

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        if tx.status == "paid":
            return {
                "transaction": str(tx.id),
                "perform_time": now_ms,
                "state": self.STATE_COMPLETED
            }

        # Obunani 30 kunga uzaytirish
        sub_repo = SubscriptionRepository(self.session, tenant_id=tx.tenant_id)
        await sub_repo.extend_subscription(
            tenant_id=tx.tenant_id,
            subscription_id=tx.subscription_id,
            days_to_add=30
        )

        await payment_repo.update_status(tx.id, "paid", raw_callback_payload=params)
        await self.session.commit()

        return {
            "transaction": str(tx.id),
            "perform_time": now_ms,
            "state": self.STATE_COMPLETED
        }

    async def cancel_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tx_id = params.get("id")
        reason = params.get("reason", 1)

        payment_repo = PaymentRepository(self.session)
        tx = await payment_repo.get_by_provider_tx(provider="payme", provider_transaction_id=tx_id)
        if not tx:
            raise PaymeException(-31003, "Tranzaksiya topilmadi")

        cancel_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        state = self.STATE_CANCELLED_AFTER_COMPLETE if tx.status == "paid" else self.STATE_CANCELLED

        await payment_repo.update_status(tx.id, "canceled", raw_callback_payload=params)
        await self.session.commit()

        return {
            "transaction": str(tx.id),
            "cancel_time": cancel_time,
            "state": state
        }

    async def check_transaction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        tx_id = params.get("id")
        payment_repo = PaymentRepository(self.session)
        tx = await payment_repo.get_by_provider_tx(provider="payme", provider_transaction_id=tx_id)
        if not tx:
            raise PaymeException(-31003, "Tranzaksiya topilmadi")

        state = self.STATE_COMPLETED if tx.status == "paid" else self.STATE_CREATED
        now_ms = int(tx.created_at.timestamp() * 1000)

        return {
            "create_time": now_ms,
            "perform_time": now_ms if tx.status == "paid" else 0,
            "cancel_time": 0,
            "transaction": str(tx.id),
            "state": state,
            "reason": None
        }

    def _error_response(self, code: int, message: str, req_id: Any) -> Dict[str, Any]:
        return {
            "error": {
                "code": code,
                "message": {"uz": message, "ru": message, "en": message}
            },
            "id": req_id
        }


class PaymeException(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
