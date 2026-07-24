from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.users.repository import UserRepository, create_jwt_token, create_refresh_token
from users import schemas
from users.models import User, UserProfile

from dependecies import password_hash
from users.schemas import UserProfileUpdate


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def register(self, data: schemas.UserRegister):

        user = self.repository.get_by_email(data.email)

        if user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = password_hash.hash(data.password)

        new_user = User(
            email=data.email,
            hashed_password=hashed_password,
            group_id=1,
        )

        user = self.repository.create_user(new_user)

        profile = UserProfile(
            user_id=user.id,
        )

        self.repository.create_profile(profile)

        return user

    def authenticate(
        self,
        email: str,
        password: str,
    ):
        user = self.repository.get_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        verified_password = password_hash.verify(password, user.hashed_password)

        if not verified_password:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        return user

    def login(self, data: schemas.UserLogin):

        user = self.authenticate(data.email, data.password)

        access_and_refresh = create_jwt_token(user)

        self.repository.save_refresh_token(access_and_refresh["refresh_token"])

        return access_and_refresh

    def refresh(self, user: User):

        refresh_token = self.repository.get_refresh_token(user.refresh_tokens)

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is invalid")

        create_jwt_token(user)

        return

    def logout(self, user: User):

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        refresh_token = self.repository.get_refresh_token(user.refresh_tokens)

        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh token is invalid")

        self.repository.delete_refresh_token(user.refresh_tokens)

    def get_me(self, user: User):

        user = self.repository.get_by_email(user.email)

        if not user:
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        return user

    def update_profile(self, profile: UserProfileUpdate):

        self.repository.update_profile(profile)

    def activate_account(self, user: User): ...

    def forgot_password(self, user: User): ...

    def reset_password(self, user: User): ...

    def change_password(self, user: User): ...
