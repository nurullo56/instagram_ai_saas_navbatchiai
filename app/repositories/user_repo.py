import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session, tenant_id=None)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).filter(User.email == email.lower().strip())
        result = await self.session.execute(query)
        return result.scalars().first()
