import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Text, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, Index, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class FlowDefinition(Base, TimestampMixin, TenantMixin):
    __tablename__ = "flow_definitions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_flow_account"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_flow_definitions_composite"),
    )


class FlowVersion(Base, TenantMixin):
    __tablename__ = "flow_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(100), nullable=False)  # keyword_dm, comment_keyword, story_mention
    trigger_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    nodes: Mapped[list] = mapped_column(JSONB, nullable=False)
    edges: Mapped[list] = mapped_column(JSONB, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "flow_definition_id"],
            ["flow_definitions.tenant_id", "flow_definitions.id"],
            ondelete="RESTRICT",
            name="fk_flow_version_def"
        ),
        UniqueConstraint("tenant_id", "flow_definition_id", "version_number", name="uq_flow_version_num"),
        UniqueConstraint("tenant_id", "id", name="uq_flow_versions_composite"),
    )


class FlowExecution(Base, TenantMixin):
    __tablename__ = "flow_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flow_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    flow_definition_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    recipient_id: Mapped[str] = mapped_column(String(100), nullable=False)
    trigger_source: Mapped[str] = mapped_column(String(50), default="webhook", nullable=False)  # webhook, manual, api
    trigger_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    context_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # running, waiting_input, completed, failed, paused
    step_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_flow_exec_account"
        ),
        ForeignKeyConstraint(
            ["tenant_id", "conversation_id"],
            ["conversations.tenant_id", "conversations.id"],
            ondelete="RESTRICT",
            name="fk_flow_exec_conversation"
        ),
        CheckConstraint(
            "((trigger_source = 'webhook' AND trigger_event_id IS NOT NULL) OR (trigger_source <> 'webhook'))",
            name="chk_webhook_trigger_id"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_flow_executions_composite"),
        Index(
            "uq_flow_exec_webhook_dedup",
            "tenant_id", "flow_definition_id", "trigger_event_id",
            unique=True,
            postgresql_where=text("trigger_source = 'webhook'")
        ),
        Index(
            "uq_active_waiting_input_flow",
            "tenant_id", "conversation_id",
            unique=True,
            postgresql_where=text("status = 'waiting_input'")
        ),
    )
