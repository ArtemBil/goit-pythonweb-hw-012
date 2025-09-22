from typing import Optional

from sqlalchemy import Column, String, Integer, Date, Text, UniqueConstraint, ForeignKey, CheckConstraint, Boolean, \
    DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

"""SQLAlchemy ORM models for contacts and users."""

class Contact(Base):
    """Contact entity representing an address book contact."""
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("email", name="uq_contacts_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[str] = mapped_column(String(32))
    birthday: Mapped[Date] = mapped_column(Date)
    extra: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    user: Mapped['User'] = relationship('User')

class User(Base):
    """User entity representing an application user with roles and avatar."""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    password: Mapped[str] = mapped_column(String(512), nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmed = mapped_column(Boolean, default=False)
    created_at = mapped_column(DateTime, default=func.now())
    role: Mapped[str] = mapped_column(String(16), default="user")

    __table_args__ = (CheckConstraint("length(password) >=8", name="password_len_constraint"),)