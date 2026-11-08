import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class Conversation(Base, TimestampMixin, TenantMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ig_recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)  # open, resolved, pending
    mode: Mapped[str] = mapped_column(String(50), default="bot", nullable=False)  # bot, human_takeover, ai_assistant
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    messaging_window_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 24h limit
    unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_conversations_account"
        ),
        UniqueConstraint("tenant_id", "instagram_account_id", "ig_recipient_id", name="uq_conversation_recipient"),
        UniqueConstraint("tenant_id", "id", name="uq_conversations_composite"),
    )


class Message(Base, TenantMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    mid: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)  # contact, bot, human_agent, ai
    message_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="sent", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["conversations.tenant_id", "conversations.id"],
            ondelete="RESTRICT",
            name="fk_messages_conversation"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_messages_composite"),
    )
