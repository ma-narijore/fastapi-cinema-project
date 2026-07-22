import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    get_current_user, require_group, decode_token,
)


from app.users.models import ActivationToken, User, RefreshToken, PasswordResetToken
from app.users.repository import UserRepository
from app.users.schemas import (
    ActivationRequest, ResendActivationRequest, UserRegister, UserLogin,
    UserResponse, TokenResponse, ResetPasswordRequest,
    LogoutRequest, ChangeGroupRequest, UserGroup, ForgotPasswordRequest, ChangePasswordRequest
)

from app.users.tasks import send_activation_email_task, send_reset_email_task


router = APIRouter(prefix="/users", tags=["users"])


def get_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def _issue_activation_token(repo: UserRepository, user: User) -> ActivationToken:
    # a user can only hold one activation token (unique user_id); drop the old one
    existing = repo.get_activation_token_by_user(user.id)

    if existing:
        repo.delete_activation_token(existing)

    token = ActivationToken(
        user_id=user.id,
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.ACTIVATION_TOKEN_EXPIRE_HOURS),
    )

    return repo.save_activation_token(token)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    repo: UserRepository = Depends(get_repository),
):
    # ensure email uniqueness before registration
    if repo.get_by_email(data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    default_group = repo.get_or_create_group(UserGroup.USER.value)

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_active=False,
        group_id=default_group.id,
    )
    user = repo.create_user(user)

    token = _issue_activation_token(repo, user)
    send_activation_email_task.delay(user.email, token.token)

    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, repo: UserRepository = Depends(get_repository)):
    user = repo.get_by_email(data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is not active")
    access = create_access_token(str(user.id))
    refresh = create_refresh_token(str(user.id))
    repo.save_refresh_token(
        RefreshToken(
            user_id=user.id,
            token=refresh,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(data: LogoutRequest, repo: UserRepository = Depends(get_repository)):
    token = repo.get_refresh_token(data.refresh_token)
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")
    repo.delete_refresh_token(token)
    return {"message": "Logged out"}


@router.get("/activate", status_code=status.HTTP_200_OK)
def activate(
    token: str,
    repo: UserRepository = Depends(get_repository),
):
    activation_token = repo.get_activation_token(token)

    if not activation_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token",
        )

    if activation_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token expired. Request a new one.",
        )

    repo.activate_user(
        activation_token.user,
        activation_token,
    )

    return {"message": "Account activated successfully"}


@router.post("/resend-activation", status_code=status.HTTP_200_OK)
def resend_activation(
    data: ResendActivationRequest,
    repo: UserRepository = Depends(get_repository),
):
    user = repo.get_by_email(data.email)

    if user and not user.is_active:
        token = _issue_activation_token(repo, user)
        send_activation_email_task.delay(user.email, token.token)

    return {"message": "If the account exists, a new activation link was sent."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(data: ForgotPasswordRequest, repo: UserRepository = Depends(get_repository)):
    user = repo.get_by_email(data.email)

    if user:
        existing = repo.get_password_reset_token_by_user(user.id)

        if existing:
            repo.delete_password_reset_token(existing)

        token = PasswordResetToken(
            user_id=user.id,
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS),
        )
        repo.save_password_reset_token(token)

        send_reset_email_task.delay(user.email, token.token)

    return {"message": "If the account exists, a reset link was sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(
    data: ResetPasswordRequest,
    repo: UserRepository = Depends(get_repository),
):
    # complexity is already enforced by ResetPasswordRequest's validator
    token = repo.get_password_reset_token(data.token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token",
        )

    if token.expires_at < datetime.now(timezone.utc):
        repo.delete_password_reset_token(token)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired. Request a new one.",
        )

    user = token.user
    user.hashed_password = hash_password(data.new_password)

    repo.update_user(user)
    repo.delete_password_reset_token(token)

    return {"message": "Password reset successfully"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
        data: ChangePasswordRequest,
        current_user: User = Depends(get_current_user),
        repo: UserRepository = Depends(get_repository),
):
    # complexity of new_password is enforced by ChangePasswordRequest's validator
    if not verify_password(data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(data.new_password)
    repo.update_user(current_user)

    return {"message": "Password changed successfully"}


@router.get("/", response_model=list[UserResponse])
def list_users(repo: UserRepository = Depends(get_repository)):
    return repo.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    repo: UserRepository = Depends(get_repository),
):
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    repo: UserRepository = Depends(get_repository),
):
    user = repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    repo.delete_user(user)
