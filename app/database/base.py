import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Barcha ORM modellari uchun asosiy DeclarativeBase"""
    pass


class TimestampMixin:
    """Yaratilgan va yangilangan vaqtlarni avtomatik qayd etish mixini"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class TenantMixin:
    """Multi-tenant izolyatsiyasi uchun tenant_id ustuni mixini"""
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
