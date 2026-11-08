import uuid
from typing import Generic, TypeVar, Type, Optional, List, Any
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Asosiy repozitoriy sinfi.
    Agar model TenantMixin ga ega bo'lsa, barcha SELECT/UPDATE/DELETE
    so'rovlarida tenant_id filtri majburiy qo'llaniladi.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession, tenant_id: Optional[uuid.UUID] = None):
        self.model = model
        self.session = session
        self.tenant_id = tenant_id

    def _apply_tenant_filter(self, query):
        if hasattr(self.model, "tenant_id") and self.tenant_id is not None:
            return query.filter(self.model.tenant_id == self.tenant_id)
        return query

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        query = select(self.model).filter(self.model.id == id)
        query = self._apply_tenant_filter(query)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        query = select(self.model).offset(skip).limit(limit)
        query = self._apply_tenant_filter(query)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, **kwargs) -> ModelType:
        if hasattr(self.model, "tenant_id") and self.tenant_id is not None:
            kwargs["tenant_id"] = self.tenant_id
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, id: uuid.UUID, **kwargs) -> Optional[ModelType]:
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, id: uuid.UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.flush()
        return True
