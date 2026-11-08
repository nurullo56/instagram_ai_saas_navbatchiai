import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.subscription import Subscription
from app.models.payment import PaymentTransaction
from app.services.billing.payme_service import PaymeService
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


@pytest.mark.asyncio
async def test_payme_check_perform_transaction_success():
    mock_session = AsyncMock()
    service = PaymeService(mock_session)

    tenant_id = uuid.uuid4()
    sub_id = uuid.uuid4()

    sub = Subscription(
        id=sub_id,
        tenant_id=tenant_id,
        plan_id=uuid.uuid4(),
        status="active",
        billing_cycle="monthly",
        currency="UZS",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        cancel_at_period_end=False
    )

    with patch.object(SubscriptionRepository, "get_by_id", return_value=sub):
        req = {
            "method": "CheckPerformTransaction",
            "params": {
                "amount": 50000000,
                "account": {"tenant_id": str(tenant_id), "subscription_id": str(sub_id)}
            },
            "id": 101
        }
        res = await service.handle_request(req)

        assert res["result"]["allow"] is True
        assert res["id"] == 101


@pytest.mark.asyncio
async def test_payme_check_perform_transaction_missing_account():
    mock_session = AsyncMock()
    service = PaymeService(mock_session)

    req = {
        "method": "CheckPerformTransaction",
        "params": {
            "amount": 50000000,
            "account": {}  # Bo'sh
        },
        "id": 102
    }
    res = await service.handle_request(req)

    assert "error" in res
    assert res["error"]["code"] == -31001


@pytest.mark.asyncio
async def test_payme_perform_transaction_extends_subscription():
    mock_session = AsyncMock()
    service = PaymeService(mock_session)

    tenant_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    tx_id = uuid.uuid4()

    payment_tx = PaymentTransaction(
        id=tx_id,
        tenant_id=tenant_id,
        subscription_id=sub_id,
        provider="payme",
        provider_transaction_id="payme_tx_777",
        amount_minor_units=50000000,
        currency="UZS",
        status="pending",
        idempotency_key="key_1"
    )

    with patch.object(PaymentRepository, "get_by_provider_tx", return_value=payment_tx), \
         patch.object(PaymentRepository, "update_status", return_value=True) as mock_update_status, \
         patch.object(SubscriptionRepository, "extend_subscription", return_value=MagicMock()) as mock_extend:

        req = {
            "method": "PerformTransaction",
            "params": {"id": "payme_tx_777"},
            "id": 103
        }
        res = await service.handle_request(req)

        assert res["result"]["state"] == 2
        mock_extend.assert_called_once_with(tenant_id=tenant_id, subscription_id=sub_id, days_to_add=30)
        mock_update_status.assert_called_once()
