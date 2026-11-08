import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.payment import PaymentTransaction
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[PaymentTransaction]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(PaymentTransaction, session, tenant_id=tenant_id)

    async def get_by_provider_tx(
        self,
        provider: str,
        provider_transaction_id: str,
        provider_action: str = "payment"
    ) -> Optional[PaymentTransaction]:
        """Provayder tranzaksiya ID si bo'yicha to'lovni topish"""
        stmt = select(PaymentTransaction).where(
            PaymentTransaction.provider == provider,
            PaymentTransaction.provider_transaction_id == provider_transaction_id,
            PaymentTransaction.provider_action == provider_action
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create_transaction(
        self,
        tenant_id: uuid.UUID,
        subscription_id: uuid.UUID,
        provider: str,
        provider_transaction_id: str,
        amount_minor_units: int,
        currency: str,
        idempotency_key: str,
        provider_action: str = "payment",
        raw_callback_payload: Optional[Dict[str, Any]] = None
    ) -> PaymentTransaction:
        """
        To'lov tranzaksiyasini yaratish.
        ON CONFLICT DO NOTHING orqali idempotentlik ta'minlanadi.
        """
        stmt = (
            insert(PaymentTransaction)
            .values(
                tenant_id=tenant_id,
                subscription_id=subscription_id,
                provider=provider,
                provider_transaction_id=provider_transaction_id,
                provider_action=provider_action,
                amount_minor_units=amount_minor_units,
                currency=currency,
                status="pending",
                idempotency_key=idempotency_key,
                raw_callback_payload=raw_callback_payload
            )
            .on_conflict_do_nothing(
                index_elements=["provider", "provider_transaction_id", "provider_action"]
            )
            .returning(PaymentTransaction)
        )
        res = await self.session.execute(stmt)
        tx = res.scalars().first()
        if tx:
            return tx

        existing = await self.get_by_provider_tx(provider, provider_transaction_id, provider_action)
        if not existing:
            raise RuntimeError("Payment creation race condition failed to return record")
        return existing

    async def update_status(
        self,
        transaction_id: uuid.UUID,
        status: str,
        raw_callback_payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Tranzaksiya holatini yangilash (paid, canceled, failed)"""
        values: Dict[str, Any] = {"status": status}
        if raw_callback_payload:
            values["raw_callback_payload"] = raw_callback_payload

        stmt = (
            update(PaymentTransaction)
            .where(PaymentTransaction.id == transaction_id)
            .values(**values)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0
