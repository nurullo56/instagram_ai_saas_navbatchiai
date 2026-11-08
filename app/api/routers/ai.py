import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.api.dependencies import get_current_tenant
from app.models.tenant import Tenant
from app.repositories.ai_repo import AIRepository
from app.repositories.instagram_repo import InstagramAccountRepository
from app.schemas.ai import (
    AIAgentConfigResponse,
    AIAgentConfigUpdate,
    KnowledgeSourceCreate,
    KnowledgeSourceResponse,
)

router = APIRouter(prefix="/ai", tags=["AI & Knowledge Base"])


@router.get("/config/{account_id}", response_model=Optional[AIAgentConfigResponse])
async def get_ai_config(
    account_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Instagram akkaunt uchun AI konfiguratsiyasini olish"""
    ai_repo = AIRepository(session, tenant_id=tenant.id)
    config = await ai_repo.get_config_by_account(tenant.id, account_id)
    return config


@router.put("/config/{account_id}", response_model=AIAgentConfigResponse)
async def update_ai_config(
    account_id: uuid.UUID,
    data: AIAgentConfigUpdate,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Instagram akkaunt uchun AI agent konfiguratsiyasini yangilash yoki yaratish"""
    # Akkaunt tenantga tegishli ekanligini tasdiqlash
    account_repo = InstagramAccountRepository(session, tenant_id=tenant.id)
    account = await account_repo.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instagram akkaunt topilmadi")

    ai_repo = AIRepository(session, tenant_id=tenant.id)
    existing = await ai_repo.get_config_by_account(tenant.id, account_id)

    system_prompt = data.system_prompt or (existing.system_prompt if existing else "Siz do'stona AI yordamchisiz.")
    model_name = data.model_name or (existing.model_name if existing else "meta-llama/llama-3.3-70b-instruct")
    temperature = data.temperature if data.temperature is not None else (existing.temperature if existing else 0.7)
    max_tokens = data.max_tokens if data.max_tokens is not None else (existing.max_tokens if existing else 350)
    lead_capture_enabled = data.lead_capture_enabled if data.lead_capture_enabled is not None else (existing.lead_capture_enabled if existing else True)
    is_active = data.is_active if data.is_active is not None else (existing.is_active if existing else True)

    config = await ai_repo.upsert_config(
        tenant_id=tenant.id,
        instagram_account_id=account_id,
        system_prompt=system_prompt,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        lead_capture_enabled=lead_capture_enabled,
        is_active=is_active
    )
    await session.commit()
    return config


@router.post("/knowledge", response_model=KnowledgeSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_knowledge_source(
    payload: KnowledgeSourceCreate,
    tenant: Tenant = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db)
):
    """Yangi bilim manbasini (FAQ, mahsulot ma'lumotlari) qo'shish"""
    ai_repo = AIRepository(session, tenant_id=tenant.id)
    source = await ai_repo.create_knowledge_source(
        tenant_id=tenant.id,
        title=payload.title,
        source_type=payload.source_type
    )

    # 1536 o'lchamli dummy embedding (haqiqiy RAG integratsiyasida OpenRouter/OpenAI embedding chaqiriladi)
    dummy_embedding = [0.0] * 1536
    await ai_repo.add_knowledge_chunk(
        tenant_id=tenant.id,
        source_id=source.id,
        chunk_index=0,
        content=payload.content,
        embedding=dummy_embedding
    )

    await session.commit()
    return source
