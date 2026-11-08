import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.repositories.user_repo import UserRepository
from app.repositories.tenant_repo import TenantRepository
from app.security.jwt import decode_token
from app.security.tenant_context import set_current_tenant_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db)
) -> User:
    """JWT Access token orqali joriy foydalanuvchini aniqlash"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autentifikatsiya ma'lumotlari yaroqsiz",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise credentials_exception

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Foydalanuvchi hisobi topilmadi yoki bloklangan"
        )
    return user


async def get_current_tenant(
    token: str = Depends(oauth2_scheme),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> Tenant:
    """
    Joriy faol tenantni aniqlash va DB tranzaksiyasida RLS kontekstini o'rnatish.
    Frontend yuborgan headerga ko'r-ko'rona ishonilmaydi:
    foydalanuvchining ushbu tenant a'zosi ekanligi bazadan tekshiriladi!
    """
    tenant_repo = TenantRepository(session)

    # 1. Tenant ID ni tanlash (Header yoki Token ichidagi default)
    target_tenant_id: Optional[uuid.UUID] = None
    if x_tenant_id:
        try:
            target_tenant_id = uuid.UUID(x_tenant_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Noto'g'ri X-Tenant-ID formati")
    else:
        payload = decode_token(token)
        token_tenant_id = payload.get("tenant_id")
        if token_tenant_id:
            target_tenant_id = uuid.UUID(token_tenant_id)

    if not target_tenant_id:
        # Agar tokenda ham, headerda ham bo'lmasa, birinchi a'zolikni olamiz
        memberships = await tenant_repo.get_user_memberships(current_user.id)
        if not memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sizga tegishli tenant topilmadi")
        target_tenant_id = memberships[0][0].id

    # 2. Xavfsizlik tekshiruvi: foydalanuvchi haqiqatan ushbu tenant a'zosimi?
    membership = await tenant_repo.get_membership(current_user.id, target_tenant_id)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sizda ushbu tenant ma'lumotlariga kirish huquqi yo'q"
        )

    tenant = await tenant_repo.get_by_id(target_tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant faol emas")

    # 3. Asinxron ContextVar va DB RLS kontekstini o'rnatish
    set_current_tenant_id(tenant.id)
    await session.execute(
        select(func.set_config("app.current_tenant_id", str(tenant.id), True))
    )

    return tenant
