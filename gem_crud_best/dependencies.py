from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_async_session

# Simple dependency usage
# Annotated is the modern way to define dependencies in FastAPI
CurrentSession = Annotated[AsyncSession, Depends(get_async_session)]
