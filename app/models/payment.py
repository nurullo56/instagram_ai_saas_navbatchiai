import uuid
from sqlalchemy import String, BigInteger, ForeignKeyConstraint, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, TimestampMixin, TenantMixin


class PaymentTransaction(Base, TimestampMixin, TenantMixin):
    __tablename__ = "payment_transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # payme, click, stripe
    provider_transaction_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_action: Mapped[str] = mapped_column(String(50), default="payment", nullable=False)
    amount_minor_units: Mapped[int] = mapped_column(BigInteger, nullable=False)  # tiyin yoki sent
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, paid, canceled, failed
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_callback_payload: Mapped[dict] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "subscription_id"],
            ["subscriptions.tenant_id", "subscriptions.id"],
            ondelete="RESTRICT",
            name="fk_payment_subscription"
        ),
        UniqueConstraint("provider", "provider_transaction_id", "provider_action", name="uq_payment_provider_tx_action"),
        UniqueConstraint("provider", "idempotency_key", name="uq_payment_provider_idempotency"),
        UniqueConstraint("tenant_id", "id", name="uq_payment_transactions_composite"),
        CheckConstraint("amount_minor_units > 0", name="chk_positive_amount"),
    )
