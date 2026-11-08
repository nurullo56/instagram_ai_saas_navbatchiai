from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.services.tenant_service import TenantService
from app.services.auth_service import AuthService
from app.schemas.tenant import TenantResponse, TenantSwitchRequest
from app.schemas.auth import TokenResponse
from app.schemas.common import APIResponse
from app.api.dependencies import get_current_user, get_current_tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/current", response_model=APIResponse[TenantResponse])
async def get_current_active_tenant(
    tenant: Tenant = Depends(get_current_tenant)
):
    return APIResponse(
        success=True,
        data=TenantResponse.model_validate(tenant)
    )


@router.get("/list", response_model=APIResponse[List[TenantResponse]])
async def list_my_tenants(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    service = TenantService(session)
    memberships = await service.get_user_tenants(current_user.id)
    response_list = []
    for tenant, role in memberships:
        data = TenantResponse.model_validate(tenant)
        data.role = role
        response_list.append(data)
    return APIResponse(
        success=True,
        data=response_list
    )


@router.post("/switch", response_model=APIResponse[TokenResponse])
async def switch_active_tenant(
    data: TenantSwitchRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    tenant_service = TenantService(session)
    await tenant_service.verify_tenant_access(current_user.id, data.tenant_id)

    auth_service = AuthService(session)
    tokens = auth_service.generate_tokens(current_user.id, data.tenant_id)
    return APIResponse(
        success=True,
        message="Faol tashkilot almashtirildi",
        data=TokenResponse(**tokens)
    )
