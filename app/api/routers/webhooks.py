from typing import Optional
from fastapi import APIRouter, Request, Query, Header, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Meta Webhooks"])


@router.get("/instagram")
async def verify_instagram_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    session: AsyncSession = Depends(get_db)
):
    """
    Meta Webhook verifikatsiya endpointi (GET).
    Meta talabiga ko'ra, hub.challenge to'g'ridan-to'g'ri text/plain formatida qaytarilishi shart.
    """
    service = WebhookService(session)
    challenge = service.verify_webhook_challenge(
        hub_mode=hub_mode,
        hub_verify_token=hub_verify_token,
        hub_challenge=hub_challenge
    )
    return Response(content=challenge, media_type="text/plain")


@router.post("/instagram", status_code=status.HTTP_200_OK)
async def ingest_instagram_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    session: AsyncSession = Depends(get_db)
):
    """
    Meta Webhook hodisalarini qabul qilish endpointi (POST).
    HMAC SHA-256 imzosi tekshiriladi va hodisalar tranzaksion navbatga saqlanadi.
    """
    raw_payload_bytes = await request.body()
    service = WebhookService(session)
    result = await service.ingest_webhook_events(
        raw_payload_bytes=raw_payload_bytes,
        signature_header=x_hub_signature_256
    )
    return result
