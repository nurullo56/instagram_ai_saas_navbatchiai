import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class InstagramAccount(Base, TimestampMixin, TenantMixin):
    __tablename__ = "instagram_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ig_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    page_id: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)  # AES-256-GCM
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    webhook_subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "ig_user_id", name="uq_tenant_ig_account"),
        UniqueConstraint("tenant_id", "id", name="uq_instagram_accounts_composite"),
    )
