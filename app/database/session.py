from contextlib import asynccontextmanager
from typing import AsyncGenerator
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)
from app.database.connection import engine

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Standart FastAPI database dependency"""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


@asynccontextmanager
async def tenant_transaction(session: AsyncSession, tenant_id: UUID) -> AsyncGenerator[AsyncSession, None]:
    """
    Tranzaksiya doirasida 'app.current_tenant_id' ni xavfsiz o'rnatuvchi context manager.
    is_local = True parametrlari sababli tranzaksiya commit/rollback bo'lgach sessiya avtomatik tozalanadi.
    """
    async with session.begin():
        await session.execute(
            select(func.set_config("app.current_tenant_id", str(tenant_id), True))
        )
        yield session
