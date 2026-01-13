from typing import List, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from .dependencies import CurrentSession
from .schemas import UserCreate, UserResponse, UserUpdate
from .repository import UserRepository
from .database import engine, Base

# Modern Lifecycle Management using asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Create tables
    # Warning: This is for demo purposes. In production, use Alembic.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown: Dispose engine (optional but good practice)
    await engine.dispose()

app = FastAPI(
    title="Modern Async SQLAlchemy & FastAPI",
    lifespan=lifespan
)

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    session: CurrentSession
):
    repo = UserRepository(session)
    # Check if exists
    if await repo.get_user_by_email(user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return await repo.create_user(user_in)

@app.get("/users/", response_model=List[UserResponse])
async def read_users(
    session: CurrentSession,
    skip: int = 0,
    limit: int = 100
):
    repo = UserRepository(session)
    return await repo.get_users(skip=skip, limit=limit)

@app.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    session: CurrentSession
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: CurrentSession
):
    repo = UserRepository(session)
    user = await repo.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return await repo.update_user(user, user_update)

@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: CurrentSession
):
    repo = UserRepository(session)
    success = await repo.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
