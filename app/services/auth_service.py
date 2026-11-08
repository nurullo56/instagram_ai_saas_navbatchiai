import uuid
import re
from typing import Tuple, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.tenant import Tenant
from app.repositories.user_repo import UserRepository
from app.repositories.tenant_repo import TenantRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.config.settings import settings


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.tenant_repo = TenantRepository(session)

    def _slugify(self, text: str) -> str:
        slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug or "tenant"

    async def register(self, email: str, password: str, full_name: str, company_name: str) -> Tuple[User, Tenant]:
        """Yangi foydalanuvchi va uning birlamchi tenantini yaratish (Tranzaksion)"""
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ushbu email bilan foydalanuvchi allaqachon mavjud"
            )

        # 1. User yaratish
        hashed_pwd = hash_password(password)
        user = await self.user_repo.create(
            email=email.lower().strip(),
            hashed_password=hashed_pwd,
            full_name=full_name,
            is_active=True
        )

        # 2. Birlamchi Tenant yaratish
        base_slug = self._slugify(company_name)
        slug = base_slug
        counter = 1
        while await self.tenant_repo.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        tenant = await self.tenant_repo.create(
            name=company_name,
            slug=slug,
            is_active=True
        )

        # 3. Owner a'zoligini ulash
        await self.tenant_repo.add_member(tenant_id=tenant.id, user_id=user.id, role="owner")
        await self.session.commit()

        return user, tenant

    async def authenticate(self, email: str, password: str) -> Tuple[User, uuid.UUID]:
        """Login qilish va faol tenant ID sini aniqlash"""
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email yoki parol noto'g'ri"
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Foydalanuvchi hisobi faol emas"
            )

        memberships = await self.tenant_repo.get_user_memberships(user.id)
        if not memberships:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sizga tegishli faol tashkilot (tenant) topilmadi"
            )

        # Birlamchi faol tenant
        active_tenant_id = memberships[0][0].id
        return user, active_tenant_id

    def generate_tokens(self, user_id: uuid.UUID, tenant_id: uuid.UUID) -> Dict[str, Any]:
        """Access va Refresh tokenlar to'plamini qaytarish"""
        token_data = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
        }
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token({"sub": str(user_id)})
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh token orqali yangi access token berish"""
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Yaroqsiz token turi")
            user_id = uuid.UUID(payload["sub"])
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token yaroqsiz yoki muddati o'tgan")

        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Foydalanuvchi topilmadi")

        memberships = await self.tenant_repo.get_user_memberships(user.id)
        if not memberships:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Faol tenant topilmadi")

        active_tenant_id = memberships[0][0].id
        return self.generate_tokens(user.id, active_tenant_id)
