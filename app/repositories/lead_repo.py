import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead
from app.repositories.base import BaseRepository


class LeadRepository(BaseRepository[Lead]):
    def __init__(self, session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        super().__init__(Lead, session, tenant_id=tenant_id)

    async def get_by_recipient(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_recipient_id: str
    ) -> Optional[Lead]:
        """Instagram mijozi bo'yicha leadni topish"""
        stmt = select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.instagram_account_id == instagram_account_id,
            Lead.ig_recipient_id == ig_recipient_id
        )
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def upsert_lead(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: uuid.UUID,
        ig_recipient_id: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        custom_attributes: Optional[Dict[str, Any]] = None
    ) -> Lead:
        """
        Leadni kiritish yoki mavjud bo'lsa ma'lumotlarini yangilash.
        """
        attrs = custom_attributes or {}

        # Mavjud leadni tekshiramiz
        existing = await self.get_by_recipient(tenant_id, instagram_account_id, ig_recipient_id)
        if existing:
            if username and not existing.username:
                existing.username = username
            if full_name:
                existing.full_name = full_name
            if phone_number:
                existing.phone_number = phone_number
            if email:
                existing.email = email
            if attrs:
                existing_attrs = dict(existing.custom_attributes or {})
                existing_attrs.update(attrs)
                existing.custom_attributes = existing_attrs
            await self.session.flush()
            return existing

        lead = Lead(
            tenant_id=tenant_id,
            instagram_account_id=instagram_account_id,
            ig_recipient_id=ig_recipient_id,
            username=username,
            full_name=full_name,
            phone_number=phone_number,
            email=email,
            stage="new",
            custom_attributes=attrs
        )
        self.session.add(lead)
        await self.session.flush()
        return lead

    async def update_stage(
        self,
        tenant_id: uuid.UUID,
        lead_id: uuid.UUID,
        stage: str
    ) -> bool:
        """Lead bosqichini yangilash (new, contacted, qualified, won, lost)"""
        stmt = (
            update(Lead)
            .where(Lead.tenant_id == tenant_id, Lead.id == lead_id)
            .values(stage=stage)
        )
        res = await self.session.execute(stmt)
        return res.rowcount > 0

    async def list_leads(
        self,
        tenant_id: uuid.UUID,
        instagram_account_id: Optional[uuid.UUID] = None,
        stage: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Lead]:
        """Tenant bo'yicha leadlar ro'yxatini olish"""
        stmt = select(Lead).where(Lead.tenant_id == tenant_id)
        if instagram_account_id:
            stmt = stmt.where(Lead.instagram_account_id == instagram_account_id)
        if stage:
            stmt = stmt.where(Lead.stage == stage)

        stmt = stmt.order_by(Lead.created_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
