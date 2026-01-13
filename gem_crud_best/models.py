import datetime
from typing import Optional

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

# Modern SQLAlchemy 2.0 Models using Mapped[] type hints

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Server-side default for created_at
    created_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now()
    )

    # Optional field example
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
