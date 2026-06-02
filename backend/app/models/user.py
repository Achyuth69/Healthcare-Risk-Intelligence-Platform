"""
User Model — Authentication and RBAC
SQLite + PostgreSQL compatible.
"""
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.core.rbac import Role


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Store role as plain string — avoids PostgreSQL-only Enum dialect type
    role: Mapped[str] = mapped_column(String(50), nullable=False, default=Role.READONLY.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def get_role(self) -> Role:
        try:
            return Role(self.role)
        except ValueError:
            return Role.READONLY

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
