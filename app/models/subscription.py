import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_cents: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    max_instagram_accounts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_monthly_messages: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    max_ai_tokens: Mapped[int] = mapped_column(Integer, default=100000, nullable=False)
    max_flows: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    ai_features_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Subscription(Base, TimestampMixin, TenantMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # trialing, active, past_due, canceled, expired
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="USD", nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_subscriptions_tenant_id_composite"),
        Index(
            "uq_tenant_single_active_subscription",
            "tenant_id",
            unique=True,
            postgresql_where=(status.in_(["trialing", "active", "past_due"]))
        ),
    )


class SubscriptionUsageRecord(Base, TimestampMixin, TenantMixin):
    __tablename__ = "subscription_usage_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)  # messages_sent, ai_tokens_consumed, flow_executions
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "metric", "period_start", name="uq_tenant_usage_metric_period"),
    )
