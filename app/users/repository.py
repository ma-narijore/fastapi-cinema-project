from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.users.models import (
    User,
    UserProfile,
    RefreshToken,
    ActivationToken,
    PasswordResetToken,
)

from app.users.schemas import UserProfileUpdate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: EmailStr) -> User | None:
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

    def update_profile(self, profile: UserProfileUpdate) -> UserProfile | None:

        self.db.commit()
        self.db.refresh(profile)

        return (
            self.db.query(UserProfile)
            .filter(UserProfile.user_id == User.profile)
            .first()
        )

    def get_profile(self, user_id: int) -> UserProfile | None:

        return self.db.query(UserProfile).filter(UserProfile.id == user_id).first()

    def save_refresh_token(self, refresh_token: RefreshToken):
        self.db.add(refresh_token)
        self.db.commit()

        self.db.refresh(refresh_token)

        return refresh_token

    def get_refresh_token(self, token: str) -> RefreshToken | None:
        return  self.db.query(RefreshToken).filter(RefreshToken.token == token).first()

    def get_activation_token(self, token: str) -> ActivationToken | None:
        return (
            self.db.query(ActivationToken)
            .filter(ActivationToken.token == token)
            .first()
        )

    def get_activation_token_by_user(self, user_id: int) -> ActivationToken | None:
        return (
            self.db.query(ActivationToken)
            .filter(ActivationToken.user_id == user_id)
            .first()
        )

    def save_activation_token(self, token: ActivationToken) -> ActivationToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def delete_activation_token(self, token: ActivationToken) -> None:
        self.db.delete(token)
        self.db.commit()

    def activate_user(self, user: User, token: ActivationToken) -> User:
        user.is_active = True
        self.db.delete(token)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_refresh_token(self, token: RefreshToken):
        self.db.delete(token)
        self.db.commit()
        return "Refresh token deleted"

    # --- password reset tokens ---
    def get_password_reset_token(self, token: str) -> PasswordResetToken | None:
        return (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.token == token)
            .first()
        )

    def get_password_reset_token_by_user(self, user_id: int) -> PasswordResetToken | None:
        return (
            self.db.query(PasswordResetToken)
            .filter(PasswordResetToken.user_id == user_id)
            .first()
        )

    def save_password_reset_token(self, token: PasswordResetToken) -> PasswordResetToken:
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def delete_password_reset_token(self, token: PasswordResetToken) -> None:
        self.db.delete(token)
        self.db.commit()

    def get_or_create_group(self, name: str):
        from app.users.models import UserGroupModel
        group = (
            self.db.query(UserGroupModel)
            .filter(UserGroupModel.name == name)
            .first()
        )
        if not group:
            group = UserGroupModel(name=name)
            self.db.add(group)
            self.db.commit()
            self.db.refresh(group)
        return group
