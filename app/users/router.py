import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    validate_password_complexity,
)
from app.users.dependencies import get_current_user, require_admin
from app.users.email import send_activation_email, send_reset_email
from app.users.models import (
    ActivationToken,
    PasswordResetToken,
    RefreshToken,
    User,
    UserGroupModel,
)
from app.users.schemas import (
    ActivationRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    MessageRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserGroup,
    UserLogin,
    UserRegister,
    UserResponse,
)


router = APIRouter(prefix="/users", tags=["users"])


def _now():
    return datetime.now(timezone.utc)


def _new_token():
    return secrets.token_urlsafe(32)


# --- Registration -----------------------------------------------------------
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    data: UserRegister,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
): ...
