from typing import Sequence, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User
from .schemas import UserCreate, UserUpdate

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_in: UserCreate) -> User:
        # Create instance from Pydantic model
        user = User(**user_in.model_dump())
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        # Modern usage: select(Model).where(...)
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        # scalar_one_or_none returns the object or None
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = select(User).offset(skip).limit(limit).order_by(User.id)
        result = await self.session.execute(stmt)
        # scalars().all() returns a list of ORM objects
        return result.scalars().all()

    async def update_user(self, user: User, user_in: UserUpdate) -> User:
        # Update fields only if provided
        update_data = user_in.model_dump(exclude_unset=True)

        # We can update the object directly since it's attached to the session
        for key, value in update_data.items():
            setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: int) -> bool:
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0  # type: ignore
