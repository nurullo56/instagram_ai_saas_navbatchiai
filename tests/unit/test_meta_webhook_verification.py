import hmac
import hashlib
import pytest
from fastapi import HTTPException
from app.integrations.meta.webhooks import verify_meta_webhook_signature
from app.services.webhook_service import WebhookService


def test_hmac_sha256_verification_success():
    secret = "my_super_app_secret_123"
    payload = b'{"object":"instagram","entry":[]}'

    # To'g'ri imzo hosil qilish
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    header = f"sha256={mac}"

    assert verify_meta_webhook_signature(payload, header, app_secret=secret) is True


def test_hmac_sha256_verification_failure_cases():
    secret = "my_super_app_secret_123"
    payload = b'{"object":"instagram","entry":[]}'

    # 1. Noto'g'ri imzo
    assert verify_meta_webhook_signature(payload, "sha256=invalidhexsignature", app_secret=secret) is False

    # 2. Buzilgan payload (Tampered payload)
    mac = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_meta_webhook_signature(b'{"tampered":true}', f"sha256={mac}", app_secret=secret) is False

    # 3. Noto'g'ri header formati
    assert verify_meta_webhook_signature(payload, "invalid_format", app_secret=secret) is False
    assert verify_meta_webhook_signature(payload, "", app_secret=secret) is False


def test_webhook_challenge_verification():
    from unittest.mock import MagicMock
    service = WebhookService(session=MagicMock())

    # Muvaffaqiyatli verifikatsiya
    from app.config.settings import settings
    challenge = service.verify_webhook_challenge(
        hub_mode="subscribe",
        hub_verify_token=settings.META_WEBHOOK_VERIFY_TOKEN,
        hub_challenge="1158201244"
    )
    assert challenge == "1158201244"

    # Noto'g'ri token bilan rad etilishi
    with pytest.raises(HTTPException) as exc_info:
        service.verify_webhook_challenge(
            hub_mode="subscribe",
            hub_verify_token="wrong_token",
            hub_challenge="1158201244"
        )
    assert exc_info.value.status_code == 403
