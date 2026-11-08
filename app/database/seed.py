import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.subscription import Plan, Subscription
from app.models.tenant import Tenant, TenantMembership
from app.models.user import User
from app.models.ai_config import AIAgentConfig
from app.security.password import hash_password
from app.config.logging import logger


async def seed_database():
    """Boshlang'ich tarif rejalari va superuser yaratish skripti"""
    async with async_session_factory() as session:
        # 1. Standart Tarif Rejalari (Plans)
        plans_data = [
            {
                "code": "starter",
                "name": "Starter",
                "price_cents": 1900,  # $19
                "currency": "USD",
                "max_instagram_accounts": 1,
                "max_monthly_messages": 1000,
                "max_ai_tokens": 50000,
                "max_flows": 3,
                "ai_features_enabled": False
            },
            {
                "code": "pro",
                "name": "Pro",
                "price_cents": 4900,  # $49
                "currency": "USD",
                "max_instagram_accounts": 3,
                "max_monthly_messages": 10000,
                "max_ai_tokens": 200000,
                "max_flows": 20,
                "ai_features_enabled": True
            },
            {
                "code": "enterprise",
                "name": "Enterprise",
                "price_cents": 14900,  # $149
                "currency": "USD",
                "max_instagram_accounts": 10,
                "max_monthly_messages": 50000,
                "max_ai_tokens": 1000000,
                "max_flows": 100,
                "ai_features_enabled": True
            }
        ]

        for p_data in plans_data:
            stmt = select(Plan).where(Plan.code == p_data["code"])
            existing = (await session.execute(stmt)).scalars().first()
            if not existing:
                plan = Plan(**p_data, is_active=True)
                session.add(plan)
                logger.info(f"Plan yaratildi: {p_data['name']}")

        await session.commit()

        # 2. Boshlang'ich Superuser
        user_stmt = select(User).where(User.email == "admin@saas.com")
        existing_user = (await session.execute(user_stmt)).scalars().first()
        if not existing_user:
            admin_user = User(
                email="admin@saas.com",
                hashed_password=hash_password("AdminSecurePassword2026!"),
                full_name="Bosh Administrator",
                is_active=True,
                is_superadmin=True
            )
            session.add(admin_user)
            await session.flush()

            # 3. Boshlang'ich Tenant
            tenant = Tenant(
                name="Demo Kompaniya",
                slug="demo-company",
                is_active=True
            )
            session.add(tenant)
            await session.flush()

            # 4. A'zolik (Owner)
            membership = TenantMembership(
                tenant_id=tenant.id,
                user_id=admin_user.id,
                role="owner"
            )
            session.add(membership)

            # 5. Pro obuna
            pro_plan_stmt = select(Plan).where(Plan.code == "pro")
            pro_plan = (await session.execute(pro_plan_stmt)).scalars().first()
            if pro_plan:
                now = datetime.now(timezone.utc)
                sub = Subscription(
                    tenant_id=tenant.id,
                    plan_id=pro_plan.id,
                    status="active",
                    billing_cycle="monthly",
                    currency="USD",
                    current_period_start=now,
                    current_period_end=now + timedelta(days=365)
                )
                session.add(sub)

            await session.commit()
            logger.info("Boshlang'ich Superuser va Demo Kompaniya muvaffaqiyatli yaratildi! ✅")


if __name__ == "__main__":
    asyncio.run(seed_database())
