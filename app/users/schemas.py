from pydantic import BaseModel, EmailStr, Field, field_validator

from datetime import datetime, date

from enum import Enum

from app.core.security import validate_password_complexity  # or inline the regex


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check(cls, v):
        validate_password_complexity(v)
        return v


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _check(cls, v):
        validate_password_complexity(v)
        return v


class UserGroup(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"


class Gender(str, Enum):
    MAN = "man"
    WOMAN = "woman"


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    @field_validator("password")
    @classmethod
    def _check(cls, v):
        validate_password_complexity(v)
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }


class UserProfileResponse(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    avatar: str | None = None
    gender: Gender | None = None
    date_of_birth: date | None = None
    info: str | None = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    avatar: str | None = None
    gender: Gender | None = None
    date_of_birth: date | None = None
    info: str | None = None


class CurrentUserUpdate(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    group: UserGroup
    profile: UserProfileResponse | None

    model_config = {"from_attributes": True}


class ActivationRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class MessageRequest(BaseModel):
    message: str


class ResendActivationRequest(BaseModel):
    email: EmailStr


class LogoutRequest(BaseModel):
    refresh_token: str


class ChangeGroupRequest(BaseModel):
    group: UserGroup
