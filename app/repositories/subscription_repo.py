import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Plan, Subscription, SubscriptionUsageRecord
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(Subscription, session, tenant_id=tenant_id)

    async def get_all_active_plans(self) -> List[Plan]:
        """Barcha faol tarif rejalarini olish"""
        stmt = select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.price_cents.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_plan_by_code(self, code: str) -> Optional[Plan]:
        """Tarif rejasini kod bo'yicha topish (masalan: 'starter', 'pro', 'enterprise')"""
        stmt = select(Plan).where(Plan.code == code, Plan.is_active.is_(True))
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def get_active_subscription(self, tenant_id: uuid.UUID) -> Optional[Subscription]:
        """Tenantning joriy faol obunasini olish"""
        stmt = select(Subscription).where(
            Subscription.tenant_id == tenant_id,
            Subscription.status.in_(["trialing", "active", "past_due"])
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def create_subscription(
        self,
        tenant_id: uuid.UUID,
        plan_id: uuid.UUID,
        billing_cycle: str = "monthly",
        currency: str = "USD",
        status: str = "active",
        duration_days: int = 30
    ) -> Subscription:
        """Yangi obuna yaratish yoki faollashtirish"""
        now = datetime.now(timezone.utc)
        period_end = now + timedelta(days=duration_days)

        sub = Subscription(
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=status,
            billing_cycle=billing_cycle,
            currency=currency,
            current_period_start=now,
            current_period_end=period_end,
            cancel_at_period_end=False
        )
        self.session.add(sub)
        await self.session.flush()
        return sub

    async def extend_subscription(
        self,
        tenant_id: uuid.UUID,
        subscription_id: uuid.UUID,
        days_to_add: int = 30
    ) -> Optional[Subscription]:
        """Obunani to'lov qilinganda uzaytirish"""
        stmt = select(Subscription).where(
            Subscription.tenant_id == tenant_id,
            Subscription.id == subscription_id
        )
        res = await self.session.execute(stmt)
        sub = res.scalars().first()
        if not sub:
            return None

        now = datetime.now(timezone.utc)
        # Agar muddati o'tib ketgan bo'lsa hozirdan, aks holda oldingi tugash sanasidan qo'shiladi
        base_time = max(now, sub.current_period_end)
        sub.current_period_end = base_time + timedelta(days=days_to_add)
        sub.status = "active"
        await self.session.flush()
        return sub

    async def record_usage(
        self,
        tenant_id: uuid.UUID,
        metric: str,
        quantity: int = 1
    ) -> None:
        """Metrika sarfini yozish (messages_sent, ai_tokens_consumed)"""
        now = datetime.now(timezone.utc)
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1)

        stmt = (
            insert(SubscriptionUsageRecord)
            .values(
                tenant_id=tenant_id,
                metric=metric,
                period_start=period_start,
                period_end=period_end,
                quantity=quantity
            )
            .on_conflict_do_update(
                index_elements=["tenant_id", "metric", "period_start"],
                set_={"quantity": SubscriptionUsageRecord.quantity + quantity}
            )
        )
        await self.session.execute(stmt)
