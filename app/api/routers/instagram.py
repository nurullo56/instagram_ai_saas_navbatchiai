import uuid
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.tenant import Tenant
from app.services.instagram_service import InstagramService
from app.schemas.instagram import (
    InstagramOAuthUrlResponse,
    InstagramOAuthExchangeRequest,
    InstagramAccountResponse
)
from app.schemas.common import APIResponse
from app.api.dependencies import get_current_tenant

router = APIRouter(prefix="/instagram", tags=["Instagram Accounts"])


@router.get("/oauth/url", response_model=APIResponse[InstagramOAuthUrlResponse])
async def get_oauth_url(
    redirect_uri: str = Query(..., description="Meta qaytaruvchi redirect_uri"),
    state: str = Query(..., description="CSRF himoyasi uchun state tokeni"),
    current_tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    service = InstagramService(session, tenant_id=current_tenant.id)
    url = service.get_oauth_authorization_url(redirect_uri, state)
    return APIResponse(
        success=True,
        data=InstagramOAuthUrlResponse(authorization_url=url)
    )


@router.post("/oauth/exchange", response_model=APIResponse[List[InstagramAccountResponse]], status_code=status.HTTP_201_CREATED)
async def exchange_oauth_code(
    data: InstagramOAuthExchangeRequest,
    current_tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    service = InstagramService(session, tenant_id=current_tenant.id)
    accounts = await service.connect_accounts_from_oauth(
        tenant_id=current_tenant.id,
        code=data.code,
        redirect_uri=data.redirect_uri
    )
    return APIResponse(
        success=True,
        message=f"{len(accounts)} ta Instagram hisobi muvaffaqiyatli ulandi",
        data=[InstagramAccountResponse.model_validate(acc) for acc in accounts]
    )


@router.get("/accounts", response_model=APIResponse[List[InstagramAccountResponse]])
async def list_instagram_accounts(
    current_tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    service = InstagramService(session, tenant_id=current_tenant.id)
    accounts = await service.get_tenant_accounts()
    return APIResponse(
        success=True,
        data=[InstagramAccountResponse.model_validate(acc) for acc in accounts]
    )


@router.delete("/accounts/{account_id}", response_model=APIResponse[bool])
async def disconnect_instagram_account(
    account_id: uuid.UUID,
    current_tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    service = InstagramService(session, tenant_id=current_tenant.id)
    result = await service.disconnect_account(account_id)
    return APIResponse(
        success=True,
        message="Instagram akkaunt muvaffaqiyatli uzildi",
        data=result
    )
