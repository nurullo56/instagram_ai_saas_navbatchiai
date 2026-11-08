import uuid
import hmac
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.services.billing.stripe_service import StripeService
from app.models.payment import PaymentTransaction
from app.repositories.subscription_repo import SubscriptionRepository
from app.repositories.payment_repo import PaymentRepository


def test_stripe_verify_webhook_signature():
    service = StripeService(AsyncMock(), webhook_secret="whsec_test_secret")

    payload = b'{"type": "invoice.payment_succeeded"}'
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    sig = hmac.new(b"whsec_test_secret", signed_payload, hashlib.sha256).hexdigest()
    sig_header = f"t={timestamp},v1={sig}"

    assert service.verify_webhook_signature(payload, sig_header) is True
    assert service.verify_webhook_signature(payload, f"t={timestamp},v1=wrong_sig") is False


@pytest.mark.asyncio
async def test_stripe_handle_webhook_checkout_completed():
    mock_session = AsyncMock()
    service = StripeService(mock_session, webhook_secret="whsec_test_secret")

    tenant_id = uuid.uuid4()
    sub_id = uuid.uuid4()
    tx_id = uuid.uuid4()

    event_data = {
        "id": "evt_123",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "amount_total": 4900,
                "currency": "usd",
                "metadata": {
                    "tenant_id": str(tenant_id),
                    "subscription_id": str(sub_id)
                }
            }
        }
    }

    payment_tx = PaymentTransaction(
        id=tx_id,
        tenant_id=tenant_id,
        subscription_id=sub_id,
        provider="stripe",
        provider_transaction_id="cs_test_123",
        amount_minor_units=4900,
        currency="USD",
        status="pending",
        idempotency_key="stripe_1"
    )

    with patch.object(PaymentRepository, "create_transaction", return_value=payment_tx), \
         patch.object(PaymentRepository, "update_status", return_value=True) as mock_update_status, \
         patch.object(SubscriptionRepository, "extend_subscription", return_value=MagicMock()) as mock_extend:

        res = await service.handle_webhook_event(event_data)

        assert res["status"] == "success"
        assert res["transaction_id"] == str(tx_id)
        mock_extend.assert_called_once_with(tenant_id, sub_id, days_to_add=30)
        mock_update_status.assert_called_once()
