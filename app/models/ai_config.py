import uuid
from typing import Optional
from sqlalchemy import String, Integer, Numeric, Boolean, Text, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from app.database.base import Base, TimestampMixin, TenantMixin


class AIAgentConfig(Base, TimestampMixin, TenantMixin):
    __tablename__ = "ai_agent_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instagram_account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="meta-llama/llama-3.3-70b-instruct", nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    temperature: Mapped[float] = mapped_column(Numeric(2, 1), default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=350, nullable=False)
    lead_capture_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "instagram_account_id"],
            ["instagram_accounts.tenant_id", "instagram_accounts.id"],
            ondelete="RESTRICT",
            name="fk_ai_config_account"
        ),
        UniqueConstraint("tenant_id", "instagram_account_id", name="uq_ai_config_account"),
        UniqueConstraint("tenant_id", "id", name="uq_ai_agent_configs_composite"),
    )


class KnowledgeSource(Base, TimestampMixin, TenantMixin):
    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, docx, txt, faq, raw_text
    storage_provider: Mapped[str] = mapped_column(String(50), default="s3", nullable=False)
    storage_bucket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sha256_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    error_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_knowledge_sources_composite"),
    )


class KnowledgeChunk(Base, TimestampMixin, TenantMixin):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_provider: Mapped[str] = mapped_column(String(50), default="openai", nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), default="text-embedding-3-small", nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(Integer, default=1536, nullable=False)
    embedding = mapped_column(Vector(1536), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "source_id"],
            ["knowledge_sources.tenant_id", "knowledge_sources.id"],
            ondelete="CASCADE",
            name="fk_chunks_source"
        ),
        UniqueConstraint("tenant_id", "id", name="uq_knowledge_chunks_composite"),
        CheckConstraint("embedding_dimension = 1536", name="chk_embedding_dimension_match"),
    )
