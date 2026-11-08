import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.subscription import Subscription
from app.models.payment import PaymentTransaction
from app.services.billing.click_service import ClickService
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


def test_click_verify_signature():
    service = ClickService(AsyncMock(), secret_key="my_secret")

    click_trans_id = "1001"
    service_id = "50"
    merchant_trans_id = "order_1"
    amount = "50000"
    action = "0"
    sign_time = "2026-11-08 12:00:00"

    raw_str = f"{click_trans_id}{service_id}my_secret{merchant_trans_id}{amount}{action}{sign_time}"
    valid_sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

    assert service.verify_signature(
        click_trans_id, service_id, merchant_trans_id, amount, action, sign_time, valid_sign
    ) is True

    assert service.verify_signature(
        click_trans_id, service_id, merchant_trans_id, amount, action, sign_time, "wrong_sign"
    ) is False


@pytest.mark.asyncio
async def test_click_handle_prepare_success():
    mock_session = AsyncMock()
    service = ClickService(mock_session, secret_key="my_secret")

    tenant_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    tx_id = uuid.uuid4()

    click_trans_id = "2002"
    service_id = "50"
    merchant_trans_id = f"{tenant_id}:{sub_id}"
    amount = "100000"
    action = "0"
    sign_time = "2026-11-08 12:00:00"

    raw_str = f"{click_trans_id}{service_id}my_secret{merchant_trans_id}{amount}{action}{sign_time}"
    sign_string = hashlib.md5(raw_str.encode("utf-8")).hexdigest()

    sub = Subscription(
        id=sub_id,
        tenant_id=tenant_id,
        plan_id=uuid.uuid4(),
        status="active",
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30)
    )

    payment_tx = PaymentTransaction(
        id=tx_id,
        tenant_id=tenant_id,
        subscription_id=sub_id,
        provider="click",
        provider_transaction_id=click_trans_id,
        amount_minor_units=10000000,
        currency="UZS",
        status="pending",
        idempotency_key="click_1"
    )

    with patch.object(SubscriptionRepository, "get_by_id", return_value=sub), \
         patch.object(PaymentRepository, "create_transaction", return_value=payment_tx):

        data = {
            "click_trans_id": click_trans_id,
            "service_id": service_id,
            "merchant_trans_id": merchant_trans_id,
            "amount": amount,
            "action": action,
            "sign_time": sign_time,
            "sign_string": sign_string
        }
        res = await service.handle_prepare(data)

        assert res["error"] == 0
        assert res["merchant_prepare_id"] == str(tx_id)
