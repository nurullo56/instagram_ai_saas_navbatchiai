import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class CommentLog(Base, TimestampMixin, TenantMixin):
    __tablename__ = "comment_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ig_comment_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ig_media_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ig_user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    ig_comment_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # Asl izoh vaqti
    private_reply_status: Mapped[str] = mapped_column(String(50), default="none", nullable=False)
    # none, pending, sending, sent, failed_permanent, failed_retryable, unknown
    private_reply_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    private_reply_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    private_reply_lease_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    private_reply_locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    private_reply_locked_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    private_reply_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_comment_logs_account"
        ),
        UniqueConstraint("tenant_id", "ig_comment_id", name="uq_tenant_comment"),
        UniqueConstraint("tenant_id", "id", name="uq_comment_logs_composite"),
    )
