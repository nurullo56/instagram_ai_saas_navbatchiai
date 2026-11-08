import pytest
import respx
import httpx
from app.integrations.meta.oauth import MetaOAuthService
from app.integrations.meta.client import MetaGraphClient
from app.integrations.meta.exceptions import (
    MetaRateLimitException,
    MetaAuthException,
    MetaMessagingWindowException,
    MetaPermanentException,
    classify_meta_error
)
from app.config.settings import settings


def test_meta_oauth_authorization_url():
    service = MetaOAuthService()
    url = service.get_authorization_url("https://myapp.com/callback", "csrf_state_token_123")

    assert "https://www.facebook.com" in url
    assert f"client_id={settings.META_APP_ID}" in url
    assert "instagram_manage_messages" in url
    assert "instagram_manage_comments" in url
    assert "state=csrf_state_token_123" in url


def test_meta_error_classification():
    # 1. Rate Limit
    rate_err = classify_meta_error(429, {"error": {"code": 4, "message": "App rate limit reached"}})
    assert isinstance(rate_err, MetaRateLimitException)

    # 2. Token Expired
    auth_err = classify_meta_error(400, {"error": {"code": 190, "error_subcode": 463, "message": "Token expired"}})
    assert isinstance(auth_err, MetaAuthException)

    # 3. 24h Window Violation
    window_err = classify_meta_error(400, {"error": {"code": 10, "error_subcode": 2018028, "message": "Outside 24 hour window"}})
    assert isinstance(window_err, MetaMessagingWindowException)

    # 4. Permanent error
    perm_err = classify_meta_error(400, {"error": {"code": 100, "message": "Invalid parameter"}})
    assert isinstance(perm_err, MetaPermanentException)


@pytest.mark.asyncio
@respx.mock
async def test_meta_client_get_success():
    client = MetaGraphClient()
    mock_url = f"{settings.meta_api_endpoint}/me/accounts"

    respx.get(mock_url).respond(
        status_code=200,
        json={"data": [{"id": "page_123", "name": "My Page"}]}
    )

    data = await client.get("me/accounts", access_token="test_token")
    assert len(data["data"]) == 1
    assert data["data"][0]["name"] == "My Page"
