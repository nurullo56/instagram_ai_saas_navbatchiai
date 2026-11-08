import hmac
import hashlib
from app.config.settings import settings
from app.config.logging import logger


def verify_meta_webhook_signature(
    raw_payload: bytes,
    signature_header: str,
    app_secret: str = settings.META_APP_SECRET
) -> bool:
    """
    Meta Webhook POST so'rovining 'X-Hub-Signature-256' sarlavhasini tekshirish.
    Format: sha256=<hex_digest>
    """
    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Webhook sarlavhasida sha256= imzosi mavjud emas")
        return False

    expected_signature = signature_header[7:].strip()
    mac = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_payload,
        digestmod=hashlib.sha256
    )
    computed_signature = mac.hexdigest()

    # Doimiy vaqtli (timing-attack resistant) taqqoslash
    is_valid = hmac.compare_digest(computed_signature, expected_signature)
    if not is_valid:
        logger.warning(
            "Webhook imzosi mos kelmadi",
            expected=expected_signature[:10] + "...",
            computed=computed_signature[:10] + "..."
        )
    return is_valid
