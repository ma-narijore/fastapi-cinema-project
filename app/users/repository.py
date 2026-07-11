from pydantic.v1 import EmailStr
from sqlalchemy.orm import Session

from app.users.models import (
    User,
    UserProfile,
    RefreshToken,
)


class UserRepository:

    def __init__(self, db: Session):
        self.db = db


    def get_by_id(self, user_id: int) -> User | None:
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )


    def get_by_email(self, email: EmailStr) -> User | None:
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

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

        return (
            self.db.query(User)
            .all()
        )


    def create_profile(self, profile: UserProfile) -> UserProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile


    def get_profile(self, user_id: int) -> UserProfile | None:

        return (
            self.db.query(UserProfile)
            .filter(
                UserProfile.id == user_id
            )
            .first()
        )


    def save_refresh_token(self, refresh_token: RefreshToken):
        self.db.add(refresh_token)
        self.db.commit()

        self.db.refresh(refresh_token)

        return refresh_token


    def get_refresh_token(self, token: str) -> RefreshToken | None:
        return (
            self.db.query(RefreshToken)
            .first(
                RefreshToken.token == token
            )
            .first()
        )


    def delete_refresh_token(self, token: str):

        self.db.delete(token)
        self.db.commit()

        return "Refresh token deleted"
