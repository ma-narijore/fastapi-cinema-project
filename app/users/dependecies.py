from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

from pwdlib import PasswordHash


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()

password_hash = PasswordHash.recommended()
