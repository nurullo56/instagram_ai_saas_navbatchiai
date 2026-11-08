import pytest
import respx
import httpx
from app.integrations.openrouter.client import (
    OpenRouterClient,
    OpenRouterException,
    OpenRouterRateLimitException,
)


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_successful_completion():
    client = OpenRouterClient(api_key="sk-or-test-key")

    mock_response = {
        "id": "gen-12345",
        "model": "meta-llama/llama-3.3-70b-instruct",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Assalomu alaykum! Kursimiz narxi 500,000 so'm."
                }
            }
        ],
        "usage": {
            "prompt_tokens": 45,
            "completion_tokens": 18,
            "total_tokens": 63
        }
    }

    respx.post("https://openrouter.ai/api/v1/chat/completions").respond(
        status_code=200,
        json=mock_response
    )

    result = await client.complete(
        messages=[{"role": "user", "content": "kurs narxi qancha?"}],
        model="meta-llama/llama-3.3-70b-instruct"
    )

    assert result["content"] == "Assalomu alaykum! Kursimiz narxi 500,000 so'm."
    assert result["model"] == "meta-llama/llama-3.3-70b-instruct"
    assert result["usage"]["total_tokens"] == 63


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_rate_limit_429():
    client = OpenRouterClient(api_key="sk-or-test-key")

    respx.post("https://openrouter.ai/api/v1/chat/completions").respond(
        status_code=429,
        json={"error": {"message": "Rate limit exceeded"}}
    )

    with pytest.raises(OpenRouterRateLimitException):
        await client.complete(messages=[{"role": "user", "content": "salom"}])


@pytest.mark.asyncio
@respx.mock
async def test_openrouter_client_server_error_500():
    client = OpenRouterClient(api_key="sk-or-test-key")

    respx.post("https://openrouter.ai/api/v1/chat/completions").respond(
        status_code=500,
        json={"error": {"message": "Internal server error"}}
    )

    with pytest.raises(OpenRouterException) as exc_info:
        await client.complete(messages=[{"role": "user", "content": "salom"}])

    assert exc_info.value.status_code == 500
