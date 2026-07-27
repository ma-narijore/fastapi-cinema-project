from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    validate_password_complexity,
    verify_password,
)
from app.users.models import ActivationToken, PasswordResetToken, User
from app.users.repository import UserRepository
from app.users.schemas import UserGroup


VALID_PASSWORD = "Str0ng!Pass"

Unit
tests: utility
functions and data
validation
logic


# ---------------------------------------------------------------------------
class TestPasswordHashing:
    def test_hash_is_not_plaintext_and_verifies(self):
        hashed = hash_password(VALID_PASSWORD)
        assert hashed != VALID_PASSWORD
        assert verify_password(VALID_PASSWORD, hashed) is True

    def test_verify_rejects_wrong_password(self):
        hashed = hash_password(VALID_PASSWORD)
        assert verify_password("WrongPass!1", hashed) is False


class TestPasswordComplexity:
    def test_accepts_strong_password(self):
        # Should not raise.
        validate_password_complexity(VALID_PASSWORD)

    @pytest.mark.parametrize(
        "password",
        [
            "alllowercase1!",  # no uppercase
            "ALLUPPERCASE1!",  # no lowercase
            "NoDigits!!AA",  # no digit
            "NoSpecial123A",  # no special char
            "Ab1!",  # too short
        ],
    )
    def test_rejects_weak_passwords(self, password):
        with pytest.raises(HTTPException) as exc:
            validate_password_complexity(password)
        assert exc.value.status_code == 400


class TestJWT:
    def test_access_token_roundtrip(self):
        token = create_access_token("42")
        payload = decode_token(token, "access")
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_refresh_token_roundtrip(self):
        token = create_refresh_token("7")
        payload = decode_token(token, "refresh")
        assert payload["sub"] == "7"
        assert payload["type"] == "refresh"

    def test_wrong_token_type_rejected(self):
        access = create_access_token("1")
        with pytest.raises(HTTPException) as exc:
            decode_token(access, "refresh")
        assert exc.value.status_code == 401

    def test_invalid_token_rejected(self):
        with pytest.raises(HTTPException) as exc:
            decode_token("not-a-token", "access")
        assert exc.value.status_code == 401


# ---------------------------------------------------------------------------
# Integration tests: repository interaction with the database
# ---------------------------------------------------------------------------
class TestUserRepository:
    def test_create_and_fetch_user(self, db_session):
        repo = UserRepository(db_session)
        group = repo.get_or_create_group(UserGroup.USER.value)
        user = repo.create_user(
            User(
                email="repo@example.com",
                hashed_password=hash_password(VALID_PASSWORD),
                is_active=True,
                group_id=group.id,
            )
        )
        assert user.id is not None
        assert repo.get_by_email("repo@example.com").id == user.id
        assert repo.get_by_id(user.id).email == "repo@example.com"

    def test_get_or_create_group_is_idempotent(self, db_session):
        repo = UserRepository(db_session)
        first = repo.get_or_create_group(UserGroup.ADMIN.value)
        second = repo.get_or_create_group(UserGroup.ADMIN.value)
        assert first.id == second.id


# ---------------------------------------------------------------------------
class TestRegister:
    def test_register_success(self, client):
        resp = client.post(
            "/users/register",
            json={"email": "new@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new@example.com"
        assert body["is_active"] is False
        # password must never be returned
        assert "password" not in body
        assert "hashed_password" not in body

    def test_register_duplicate_email(self, client, make_user):
        make_user(email="dup@example.com", is_active=False)
        resp = client.post(
            "/users/register",
            json={"email": "dup@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_register_weak_password_rejected(self, client):
        resp = client.post(
            "/users/register",
            json={"email": "weak@example.com", "password": "weak"},
        )
        assert resp.status_code == 400

    def test_register_invalid_email_rejected(self, client):
        resp = client.post(
            "/users/register",
            json={"email": "not-an-email", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# API endpoint tests: login (authentication workflow)
# ---------------------------------------------------------------------------
class TestLogin:
    def test_login_success_returns_tokens(self, client, make_user):
        make_user(email="login@example.com", is_active=True)
        resp = client.post(
            "/users/login",
            json={"email": "login@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["refresh_token"]
        assert body["token_type"] == "bearer"

    def test_login_wrong_password(self, client, make_user):
        make_user(email="login2@example.com", is_active=True)
        resp = client.post(
            "/users/login",
            json={"email": "login2@example.com", "password": "Wr0ng!Pass"},
        )
        assert resp.status_code == 401

    def test_login_unknown_email(self, client):
        resp = client.post(
            "/users/login",
            json={"email": "ghost@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 401

    def test_login_inactive_account_forbidden(self, client, make_user):
        make_user(email="inactive@example.com", is_active=False)
        resp = client.post(
            "/users/login",
            json={"email": "inactive@example.com", "password": VALID_PASSWORD},
        )
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# API endpoint tests: authorization / group requirements
# ---------------------------------------------------------------------------
class TestAuthorization:
    def test_list_users_requires_authentication(self, client):
        resp = client.get("/users/")
        assert resp.status_code == 401

    def test_list_users_forbidden_for_plain_user(self, client, make_user, auth_header):
        user = make_user(email="plain@example.com", group=UserGroup.USER.value)
        resp = client.get("/users/", headers=auth_header(user))
        assert resp.status_code == 403

    def test_list_users_allowed_for_moderator(self, client, make_user, auth_header):
        mod = make_user(email="mod@example.com", group=UserGroup.MODERATOR.value)
        resp = client.get("/users/", headers=auth_header(mod))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_delete_user_requires_admin(self, client, make_user, auth_header):
        mod = make_user(email="mod2@example.com", group=UserGroup.MODERATOR.value)
        victim = make_user(email="victim@example.com")
        resp = client.delete(f"/users/{victim.id}", headers=auth_header(mod))
        assert resp.status_code == 403

    def test_get_user_not_found(self, client, make_user, auth_header):
        user = make_user(email="viewer@example.com")
        resp = client.get("/users/999999", headers=auth_header(user))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# API endpoint tests: activation workflow
# ---------------------------------------------------------------------------
class TestActivation:
    def _issue_token(self, db_session, user_id, *, expired=False):
        expires = datetime.now(timezone.utc) + timedelta(hours=-1 if expired else 24)
        token = ActivationToken(
            user_id=user_id, token="activation-token", expires_at=expires
        )
        db_session.add(token)
        db_session.commit()
        return token

    def test_activate_success(self, client, make_user, db_session):
        user = make_user(email="act@example.com", is_active=False)
        self._issue_token(db_session, user.id)
        resp = client.get("/users/activate", params={"token": "activation-token"})
        assert resp.status_code == 200
        db_session.refresh(user)
        assert user.is_active is True

    def test_activate_invalid_token(self, client):
        resp = client.get("/users/activate", params={"token": "nope"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid activation token"

    def test_activate_expired_token(self, client, make_user, db_session):
        user = make_user(email="act2@example.com", is_active=False)
        self._issue_token(db_session, user.id, expired=True)
        resp = client.get("/users/activate", params={"token": "activation-token"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# API endpoint tests: password reset workflow
# ---------------------------------------------------------------------------
class TestPasswordReset:
    def test_reset_password_success(self, client, make_user, db_session):
        user = make_user(email="reset@example.com")
        token = PasswordResetToken(
            user_id=user.id,
            token="reset-token",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(token)
        db_session.commit()

        new_password = "Br4ndNew!Pw"
        resp = client.post(
            "/users/reset-password",
            json={"token": "reset-token", "new_password": new_password},
        )
        assert resp.status_code == 200
        db_session.refresh(user)
        assert verify_password(new_password, user.hashed_password)

    def test_reset_password_invalid_token(self, client):
        resp = client.post(
            "/users/reset-password",
            json={"token": "missing", "new_password": VALID_PASSWORD},
        )
        assert resp.status_code == 400

    def test_reset_password_weak_new_password(self, client):
        resp = client.post(
            "/users/reset-password",
            json={"token": "whatever", "new_password": "weak"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Functional tests: end-to-end user scenarios
# ---------------------------------------------------------------------------
class TestEndToEnd:
    def test_register_activate_login_flow(self, client, db_session):
        # 1. Register a new account (inactive by default).
        register = client.post(
            "/users/register",
            json={"email": "flow@example.com", "password": VALID_PASSWORD},
        )
        assert register.status_code == 201

        # 2. Login is blocked while the account is inactive.
        blocked = client.post(
            "/users/login",
            json={"email": "flow@example.com", "password": VALID_PASSWORD},
        )
        assert blocked.status_code == 403

        # 3. Activate using the token the register step created.
        repo = UserRepository(db_session)
        user = repo.get_by_email("flow@example.com")
        activation = repo.get_activation_token_by_user(user.id)
        assert activation is not None
        activate = client.get(
            "/users/activate", params={"token": activation.token}
        )
        assert activate.status_code == 200

        # 4. Login now succeeds and returns usable tokens.
        login = client.post(
            "/users/login",
            json={"email": "flow@example.com", "password": VALID_PASSWORD},
        )
        assert login.status_code == 200
        access = login.json()["access_token"]

        # 5. The access token authenticates against a protected endpoint.
        me = client.get(
            f"/users/{user.id}",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "flow@example.com"

    def test_forgot_then_reset_password_flow(self, client, make_user, db_session):
        make_user(email="forgot@example.com")

        # Request a reset link; response is deliberately generic.
        forgot = client.post(
            "/users/forgot-password",
            json={"email": "forgot@example.com"},
        )
        assert forgot.status_code == 200

        repo = UserRepository(db_session)
        user = repo.get_by_email("forgot@example.com")
        reset_token = repo.get_password_reset_token_by_user(user.id)
        assert reset_token is not None

        new_password = "Fr3sh!Secret"
        reset = client.post(
            "/users/reset-password",
            json={"token": reset_token.token, "new_password": new_password},
        )
        assert reset.status_code == 200

        # New password works, old one no longer does.
        ok = client.post(
            "/users/login",
            json={"email": "forgot@example.com", "password": new_password},
        )
        assert ok.status_code == 200
        old = client.post(
            "/users/login",
            json={"email": "forgot@example.com", "password": VALID_PASSWORD},
        )
        assert old.status_code == 401