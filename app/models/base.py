from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

engine = None
AsyncSessionLocal = None


class Base(DeclarativeBase):
    pass


def init_db(database_url: str):
    global engine, AsyncSessionLocal
    engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    return engine


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
