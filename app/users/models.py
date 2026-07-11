from datetime import datetime, date
from enum import Enum

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Date,
    DateTime,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.core.database import Base

class UserGroup(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Gender(str, Enum):
    MAN = "man"
    WOMAN = "woman"


class UserGroupModel(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[UserGroup] = mapped_column(
        String(50),
        unique=True,
    )

    users = relationship(
        "User",
        back_populates="group",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("user_groups.id")
    )

    group = relationship(
        "UserGroupModel",
        back_populates="users",
    )

    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
    )

    activation_token = relationship(
        "ActivationToken",
        back_populates="user",
        uselist=False,
    )

    password_reset_token = relationship(
        "PasswordResetToken",
        back_populates="user",
        uselist=False,
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
    )

    first_name: Mapped[str | None]

    last_name: Mapped[str | None]

    avatar: Mapped[str | None]

    gender: Mapped[Gender | None]

    date_of_birth: Mapped[date | None]

    info: Mapped[str | None] = mapped_column(Text)

    user = relationship(
        "User",
        back_populates="profile",
    )


class ActivationToken(Base):
    __tablename__ = "activation_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )

    expires_at: Mapped[datetime]

    user = relationship(
        "User",
        back_populates="activation_token",
    )


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )

    expires_at: Mapped[datetime]

    user = relationship(
        "User",
        back_populates="password_reset_token",
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id")
    )

    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
    )

    expires_at: Mapped[datetime]

    user = relationship(
        "User",
        back_populates="refresh_tokens",
    )
