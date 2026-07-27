from app.core.database import SessionLocal
from app.core.security import hash_password
from app.users.models import User, UserGroupModel
from app.users.schemas import UserGroup

db = SessionLocal()

admin_group = db.query(UserGroupModel).filter_by(name=UserGroup.ADMIN.value).first()

admin = User(
    email="admin@example.com",
    hashed_password=hash_password("Admin123!"),
    is_active=True,
    group=admin_group,
)

existing = db.query(User).filter_by(email="admin@example.com").first()

if existing:
    existing.group = admin_group
    existing.is_active = True
else:
    existing = User(
        email="admin@example.com",
        hashed_password=hash_password("Admin123!"),
        is_active=True,
        group=admin_group,
    )
    db.add(existing)

db.commit()

db.commit()