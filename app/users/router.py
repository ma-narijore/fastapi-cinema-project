import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


from app.users.models import ActivationToken, User
from app.users.repository import UserRepository
from app.users.schemas import (
    ActivationRequest,
    ResendActivationRequest,
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)

from app.users.tasks import send_activation_email_task


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
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_active=False,
    )
    user = repo.create_user(user)
    token = _issue_activation_token(repo, user)
    send_activation_email_task.delay(user.email, token.token)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    repo: UserRepository = Depends(get_repository),
):
    user = repo.get_by_email(data.email)

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )

    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


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


@router.post("/activate", status_code=status.HTTP_200_OK)
def activate(
    data: ActivationRequest,
    repo: UserRepository = Depends(get_repository),
):
    token = repo.get_activation_token(data.token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token",
        )

    if token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token expired. Request a new one.",
        )

    repo.activate_user(token.user, token)

    return {"message": "Account activated"}


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

