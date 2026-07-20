from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)

from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)


router = APIRouter(prefix="/users", tags=["users"])


def get_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    repo: UserRepository = Depends(get_repository),
):
    if repo.get_by_email(data.email):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    return repo.create_user(user)


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
