import hmac
import hashlib
import json
import pytest
from httpx import AsyncClient
from app.config.settings import settings


@pytest.mark.asyncio
async def test_webhook_get_verification_endpoint(client: AsyncClient):
    # 1. To'g'ri verify_token bilan (Meta challenge qaytarishi shart)
    res = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": settings.META_WEBHOOK_VERIFY_TOKEN,
            "hub.challenge": "challenge_code_987654"
        }
    )
    assert res.status_code == 200
    assert res.text == "challenge_code_987654"
    assert "text/plain" in res.headers["content-type"]

    # 2. Noto'g'ri verify_token bilan (403 Forbidden bo'lishi shart)
    res_fail = await client.get(
        "/api/v1/webhooks/instagram",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_verification_token",
            "hub.challenge": "challenge_code_987654"
        }
    )
    assert res_fail.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_signature_validation(client: AsyncClient):
    payload = {"object": "instagram", "entry": []}
    payload_bytes = json.dumps(payload).encode("utf-8")

    # 1. Imzo sarlavhasi yo'q bo'lsa (401 Unauthorized)
    res_no_sig = await client.post(
        "/api/v1/webhooks/instagram",
        content=payload_bytes
    )
    assert res_no_sig.status_code == 401

    # 2. Imzo noto'g'ri bo'lsa (401 Unauthorized)
    res_bad_sig = await client.post(
        "/api/v1/webhooks/instagram",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": "sha256=wrong_hex_signature"}
    )
    assert res_bad_sig.status_code == 401

    # 3. Imzo to'g'ri bo'lsa (200 OK)
    mac = hmac.new(settings.META_APP_SECRET.encode(), payload_bytes, hashlib.sha256).hexdigest()
    res_ok = await client.post(
        "/api/v1/webhooks/instagram",
        content=payload_bytes,
        headers={"X-Hub-Signature-256": f"sha256={mac}"}
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["status"] == "ok"
