from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.users.models import User
from app.users.schemas import UserGroup

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(token, "access")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive account")
    return user


def require_groups(*allowed: UserGroup):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.group.name not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not enough permissions")
        return user

    return checker


require_moderator = require_groups(UserGroup.MODERATOR, UserGroup.ADMIN)
require_admin = require_groups(UserGroup.ADMIN)
