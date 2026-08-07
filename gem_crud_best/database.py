from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

# 1. Create the Async Engine
# echo=True is good for learning/debugging to see generated SQL
engine = create_async_engine(
    settings.FINAL_DATABASE_URL,
    echo=settings.ECHO_SQL,
)

# 2. Create the Async Session Factory
# expire_on_commit=False is important for asyncio because
# attributes shouldn't disappear after commit() when the session is closed/awaited.
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# 3. Create the Declarative Base (Modern SQLAlchemy 2.0)
class Base(DeclarativeBase):
    pass


# 4. Helper for getting a session (to be used in Dependencies)
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
