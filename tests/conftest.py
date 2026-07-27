import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    hash_password,
)
from app.main import app
from app.users import tasks as user_tasks
from app.users.models import User
from app.users.schemas import UserGroup


@pytest.fixture()
def db_session():
    # Isolated in-memory SQLite shared across the single connection so the
    # schema and data are visible to both the test and the app under test.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def stub_email_tasks(monkeypatch):
    # Never hit Celery/Redis or SMTP during tests.
    monkeypatch.setattr(
        user_tasks.send_activation_email_task, "delay", lambda *a, **k: None
    )
    monkeypatch.setattr(
        user_tasks.send_reset_email_task, "delay", lambda *a, **k: None
    )


def _make_user(
        db_session,
        *,
        email: str,
        password: str = "Str0ng!Pass",
        is_active: bool = True,
        group: str = UserGroup.USER.value,
) -> User:
    from app.users.repository import UserRepository

    repo = UserRepository(db_session)
    group_model = repo.get_or_create_group(group)
    user = User(
        email=email,
        hashed_password=hash_password(password),
        is_active=is_active,
        group_id=group_model.id,
    )
    return repo.create_user(user)


@pytest.fixture()
def make_user(db_session):
    def _factory(**kwargs):
        return _make_user(db_session, **kwargs)

    return _factory


def _auth_header(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def auth_header():
    return _auth_header
