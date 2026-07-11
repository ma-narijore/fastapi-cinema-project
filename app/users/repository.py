import os
from datetime import datetime, timedelta, timezone
from typing import Dict

import dotenv

from jose import jwt

from pydantic.v1 import EmailStr
from sqlalchemy.orm import Session

from app.users.models import (
    User,
    UserProfile,
    RefreshToken,
)
from users.models import UserProfile, User
from users.schemas import UserResponse, UserProfileUpdate

dotenv.load_dotenv()


def create_refresh_token(user: User) -> str:

    if not user:
        raise Exception("User does not exist")

    refresh_payload = {
        "sub": user.id,
        "exp": datetime.now(timezone.utc)
        + timedelta(days=float(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))),
        "type": "refresh",
    }
    refresh_token = jwt.encode(
        refresh_payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )

    return refresh_token


def create_jwt_token(data: UserResponse) -> Dict[str, str]:
    payload = data.model_dump()

    expires_in = datetime.now(timezone.utc) + timedelta(
        minutes=float(os.getenv("JWT_EXPIRES_IN"))
    )

    payload.update({"exp": expires_in})

    jwt_token = jwt.encode(
        payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )

    refresh_token = create_refresh_token(payload)

    return {"access_token": jwt_token, "refresh_token": refresh_token}


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> type[User] | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: EmailStr) -> type[User] | None:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, user: User) -> User:

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User) -> User:

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete_user(self, user: User):

        self.db.delete(user)
        self.db.commit()

        return "User deleted"

    def get_all_users(self):

        return self.db.query(User).all()

    def create_profile(self, profile: UserProfile) -> UserProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    def update_profile(self, profile: UserProfileUpdate) -> type[UserProfile] | None:

        self.db.commit()
        self.db.refresh(profile)

        return (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == User.profile)
            .first()
        )

    def get_profile(self, user_id: int) -> type[UserProfile] | None:

        return self.db.query(UserProfile).filter(UserProfile.id == user_id).first()

    def save_refresh_token(self, refresh_token: RefreshToken):
        self.db.add(refresh_token)
        self.db.commit()

        self.db.refresh(refresh_token)

        return refresh_token

    def get_refresh_token(self, token: str) -> RefreshToken | None:
        return self.db.query(RefreshToken).first(RefreshToken.token == token).first()

    def delete_refresh_token(self, token: str):

        self.db.delete(token)
        self.db.commit()

        return "Refresh token deleted"
