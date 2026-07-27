"""Create (or ensure) an admin user.

Intended to run once on `docker compose up`, after database migrations have
been applied. Credentials are read from the environment so no secrets are
baked into the image:

    ADMIN_EMAIL     (default: admin@example.com)
    ADMIN_PASSWORD  (default: Admin123!)

The script is idempotent: if a user with ADMIN_EMAIL already exists it is
promoted to the admin group and activated instead of being recreated.
"""

import os
import sys

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import UserGroup


def create_admin() -> int:
    email = os.getenv("ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("ADMIN_PASSWORD", "Admin123!")


    db = SessionLocal()
    try:
        repo = UserRepository(db)
        # get_or_create_group guarantees the admin group exists on a fresh DB.
        admin_group = repo.get_or_create_group(UserGroup.ADMIN.value)

        existing = repo.get_by_email(email)
        if existing:
            existing.is_active = True
            existing.group_id = admin_group.id
            repo.update_user(existing)
            print(f"Admin user already exists, ensured active/admin: {email}")
            return 0


        user = User(
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            group_id=admin_group.id,
        )
        repo.create_user(user)
        print(f"Created admin user: {email}")
        return 0
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(create_admin())
    