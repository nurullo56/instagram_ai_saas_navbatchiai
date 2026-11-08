import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.dependencies import get_current_tenant
from app.models.tenant import Tenant
from app.repositories.subscription_repo import SubscriptionRepository
from app.services.billing.payme_service import PaymeService
from app.services.billing.click_service import ClickService
from app.services.billing.stripe_service import StripeService

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])


@router.post("/payme")
async def payme_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Payme JSON-RPC 2.0 webhook integratsiyasi"""
    payload = await request.json()
    service = PaymeService(session)
    return await service.handle_request(payload)


@router.post("/click/prepare")
async def click_prepare_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Click Prepare (action=0) webhook integratsiyasi"""
    # Form data yoki JSON qabul qilinadi
    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    service = ClickService(session)
    return await service.handle_prepare(data)


@router.post("/click/complete")
async def click_complete_endpoint(
    request: Request,
    session: AsyncSession = Depends(get_db)
):
    """Click Complete (action=1) webhook integratsiyasi"""
    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
    else:
        form = await request.form()
        data = dict(form)

    service = ClickService(session)
    return await service.handle_complete(data)


@router.post("/stripe/webhook")
async def stripe_webhook_endpoint(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    session: AsyncSession = Depends(get_db)
):
    """Stripe Webhook integratsiyasi"""
    raw_body = await request.body()
    service = StripeService(session)

    if not service.verify_webhook_signature(raw_body, stripe_signature or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe signature")

    event_data = await request.json()
    return await service.handle_webhook_event(event_data)


@router.get("/plans")
async def get_plans(session: AsyncSession = Depends(get_db)):
    """Mavjud barcha tarif rejalari ro'yxati"""
    repo = SubscriptionRepository(session)
    return await repo.get_all_active_plans()


@router.get("/subscription")
async def get_current_subscription(
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Tenantning joriy obunasi va holati"""
    repo = SubscriptionRepository(session, tenant_id=tenant.id)
    sub = await repo.get_active_subscription(tenant.id)
    if not sub:
        return {"status": "none", "subscription": None}
    return {"status": "active", "subscription": sub}
