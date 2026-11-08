import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db
from app.api.dependencies import get_current_tenant
from app.models.tenant import Tenant
from app.models.flow import FlowDefinition, FlowVersion
from app.repositories.flow_repo import FlowRepository
from app.repositories.instagram_repo import InstagramAccountRepository
from app.services.dag_validator import DAGValidator
from app.schemas.flow import (
    FlowCreate,
    FlowVersionCreate,
    FlowResponse,
    FlowVersionResponse,
)

router = APIRouter(prefix="/flows", tags=["Flow Builder"])


@router.post("", response_model=FlowResponse, status_code=status.HTTP_201_CREATED)
async def create_flow(
    data: FlowCreate,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Yangi avtomatizatsiya oqimini (Flow) yaratish"""
    account_repo = InstagramAccountRepository(session, tenant_id=tenant.id)
    account = await account_repo.get_by_id(data.instagram_account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instagram akkaunt topilmadi")

    flow_repo = FlowRepository(session, tenant_id=tenant.id)
    flow = await flow_repo.create_flow(
        tenant_id=tenant.id,
        instagram_account_id=data.instagram_account_id,
        name=data.name,
        description=data.description
    )
    await session.commit()
    return flow


@router.get("", response_model=List[FlowResponse])
async def list_flows(
    instagram_account_id: Optional[uuid.UUID] = None,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Tenantga tegishli barcha oqimlar ro'yxatini olish"""
    stmt = select(FlowDefinition).where(FlowDefinition.tenant_id == tenant.id)
    if instagram_account_id:
        stmt = stmt.where(FlowDefinition.instagram_account_id == instagram_account_id)
    res = await session.execute(stmt)
    return list(res.scalars().all())


@router.post("/{flow_id}/versions", response_model=FlowVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_version(
    flow_id: uuid.UUID,
    data: FlowVersionCreate,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """
    Flow ning yangi versiyasini saqlash.
    DAG grafigi (sikllar, triggerlar, adashgan nodelar) tekshiriladi.
    """
    flow_repo = FlowRepository(session, tenant_id=tenant.id)
    flow = await flow_repo.get_by_id(flow_id)
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow topilmadi")

    # DAG tekshiruvi
    is_valid, err_msg = DAGValidator.validate_flow(nodes=data.nodes, edges=data.edges)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"DAG xatosi: {err_msg}")

    # Keyingi versiya raqamini aniqlash
    stmt = (
        select(FlowVersion.version_number)
        .where(FlowVersion.tenant_id == tenant.id, FlowVersion.flow_definition_id == flow_id)
        .order_by(FlowVersion.version_number.desc())
        .limit(1)
    )
    latest_num = (await session.execute(stmt)).scalars().first() or 0
    new_version_num = latest_num + 1

    version = await flow_repo.create_version(
        tenant_id=tenant.id,
        flow_definition_id=flow_id,
        version_number=new_version_num,
        trigger_type=data.trigger_type,
        trigger_config=data.trigger_config,
        nodes=data.nodes,
        edges=data.edges
    )
    await session.commit()
    return version


@router.post("/{flow_id}/publish/{version_id}", response_model=FlowResponse)
async def publish_flow_version(
    flow_id: uuid.UUID,
    version_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Flow versiyasini nashr qilish va faollashtirish"""
    flow_repo = FlowRepository(session, tenant_id=tenant.id)
    success = await flow_repo.publish_version(tenant.id, flow_id, version_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Versiyani nashr qilib bo'lmadi")

    await session.commit()
    updated_flow = await flow_repo.get_by_id(flow_id)
    return updated_flow
