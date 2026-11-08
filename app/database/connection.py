from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.config.settings import settings

# Async Engine yaratish
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)
