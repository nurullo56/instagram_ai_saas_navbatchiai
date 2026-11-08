import os
from typing import List, Dict, Any, Optional
import httpx
from app.config.settings import settings
from app.config.logging import logger


class OpenRouterException(Exception):
    """OpenRouter xatoliklari uchun asosiy sinf"""
    def __init__(self, message: str, status_code: int = 500, raw_response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.raw_response = raw_response or {}


class OpenRouterRateLimitException(OpenRouterException):
    """OpenRouter so'rovlar limiti tugaganda (429)"""
    pass


class OpenRouterClient:
    """
    OpenRouter API mijozi:
    - Llama 3.3 70B, GPT-4o-mini, Claude 3.5 Haiku kabi modellarga so'rov yuborish
    - Avtomatik model zaxirasi (fallback)
    - Token hisobi va xarajat monitoringi
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    FALLBACK_MODELS = [
        "meta-llama/llama-3.3-70b-instruct",
        "openai/gpt-4o-mini",
        "anthropic/claude-3.5-haiku"
    ]

    def __init__(self, api_key: Optional[str] = None, timeout: float = 30.0):
        self.api_key = api_key or settings.OPENROUTER_API_KEY or os.environ.get("OPENROUTER_API_KEY", "")
        self.timeout = timeout

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 350,
        enable_fallbacks: bool = True
    ) -> Dict[str, Any]:
        """
        Chat completion so'rovini yuborish.
        Qaytaradi: {"content": "...", "model": "...", "usage": {"prompt_tokens": X, "completion_tokens": Y}}
        """
        selected_model = model or settings.DEFAULT_AI_MODEL
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://instagram-ai-saas.com",
            "X-Title": settings.APP_NAME,
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": selected_model,
            "messages": messages,
            "temperature": float(temperature),
            "max_tokens": max_tokens
        }

        if enable_fallbacks and selected_model in self.FALLBACK_MODELS:
            models_order = [selected_model] + [m for m in self.FALLBACK_MODELS if m != selected_model]
            payload["models"] = models_order

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )

                if response.status_code == 429:
                    raise OpenRouterRateLimitException("OpenRouter rate limit tugadi", status_code=429)

                if response.status_code != 200:
                    try:
                        err_json = response.json()
                    except Exception:
                        err_json = {"error": response.text}
                    raise OpenRouterException(
                        f"OpenRouter xatosi [{response.status_code}]: {err_json}",
                        status_code=response.status_code,
                        raw_response=err_json
                    )

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise OpenRouterException("OpenRouter javobida bo'sh choices qaytdi", raw_response=data)

                content = choices[0].get("message", {}).get("content", "").strip()
                used_model = data.get("model", selected_model)
                usage = data.get("usage", {})

                logger.info(
                    "OpenRouter muvaffaqiyatli javob berdi",
                    model=used_model,
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens")
                )

                return {
                    "content": content,
                    "model": used_model,
                    "usage": usage,
                    "raw": data
                }

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                logger.error("OpenRouter tarmoq xatosi", error=str(e))
                raise OpenRouterException(f"OpenRouter tarmoq xatosi: {str(e)}", status_code=504)
