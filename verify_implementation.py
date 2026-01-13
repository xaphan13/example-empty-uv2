import asyncio
import os
import sys

# Ensure we can import the package
sys.path.append(os.getcwd())

from gem_crud_best.config import settings
from gem_crud_best.database import engine, Base, async_session_factory
from gem_crud_best.repository import UserRepository
from gem_crud_best.schemas import UserCreate, UserUpdate
from sqlalchemy import text

async def verify():
    print("--- Starting Verification ---")

    # Override database URL to use SQLite for this local test in sandbox
    # since we don't have a Postgres server running.
    # The code was written for Postgres (asyncpg), but SQLAlchemy abstracts most of it.
    # However, asyncpg driver won't work with sqlite url.
    # So we need to ensure the engine uses sqlite+aiosqlite.

    # We'll re-create the engine here just for the test to ensure we use sqlite
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    sqlite_url = "sqlite+aiosqlite:///./test_verification.db"
    print(f"Using SQLite for verification: {sqlite_url}")

    test_engine = create_async_engine(sqlite_url, echo=False)
    test_session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    # Create Tables
    print("Creating tables...")
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_factory() as session:
        repo = UserRepository(session)

        # 1. Create User
        print("1. Creating User...")
        user_in = UserCreate(username="jules_dev", email="jules@example.com", full_name="Jules Agent")
        user = await repo.create_user(user_in)
        print(f"   Created: {user.id} - {user.username}")
        assert user.id is not None
        assert user.username == "jules_dev"

        # 2. Read User
        print("2. Reading User...")
        fetched_user = await repo.get_user_by_id(user.id)
        assert fetched_user is not None
        assert fetched_user.email == "jules@example.com"
        print(f"   Fetched: {fetched_user.email}")

        # 3. Update User
        print("3. Updating User...")
        update_in = UserUpdate(full_name="Jules The Great")
        updated_user = await repo.update_user(fetched_user, update_in)
        assert updated_user.full_name == "Jules The Great"
        print(f"   Updated Name: {updated_user.full_name}")

        # 4. List Users
        print("4. Listing Users...")
        users = await repo.get_users()
        print(f"   Count: {len(users)}")
        assert len(users) == 1

        # 5. Delete User
        print("5. Deleting User...")
        success = await repo.delete_user(user.id)
        assert success is True
        print("   Deleted.")

        # Verify Deletion
        deleted_user = await repo.get_user_by_id(user.id)
        assert deleted_user is None
        print("   Verification confirming deletion passed.")

    print("--- Verification Successful ---")

if __name__ == "__main__":
    asyncio.run(verify())
