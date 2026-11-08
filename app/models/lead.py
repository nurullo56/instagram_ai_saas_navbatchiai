import uuid
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class Lead(Base, TimestampMixin, TenantMixin):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ig_recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stage: Mapped[str] = mapped_column(String(50), default="new", nullable=False)  # new, contacted, qualified, won, lost
    custom_attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_leads_account"
        ),
        UniqueConstraint("tenant_id", "instagram_account_id", "ig_recipient_id", name="uq_leads_recipient"),
        UniqueConstraint("tenant_id", "id", name="uq_leads_composite"),
    )


class LeadTag(Base, TimestampMixin):
    __tablename__ = "lead_tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(20), default="#6366F1", nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_lead_tag_name"),
        UniqueConstraint("tenant_id", "id", name="uq_lead_tags_composite"),
    )


class LeadTagMapping(Base, TimestampMixin):
    __tablename__ = "lead_tag_mappings"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    lead_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tag_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "lead_id"],
            ["leads.tenant_id", "leads.id"],
            ondelete="CASCADE",
            name="fk_mapping_lead"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "tag_id"],
            ["lead_tags.tenant_id", "lead_tags.id"],
            ondelete="CASCADE",
            name="fk_mapping_tag"
        ),
    )
