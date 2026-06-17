from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


if not settings.database_url:
    async_engine = None
    AsyncSessionLocal = None
else:
    async_engine = create_async_engine(settings.database_url, future=True)
    AsyncSessionLocal = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


class Base(DeclarativeBase):
    pass


async def get_async_session() -> AsyncIterator[AsyncSession]:
    if AsyncSessionLocal is None:
        raise RuntimeError("DATABASE_URL is required to use the async persistence layer.")

    async with AsyncSessionLocal() as session:
        yield session
