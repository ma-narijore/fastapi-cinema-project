from datetime import datetime, timezone


from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.email_service import send_activation_email, send_reset_email
from app.users.models import ActivationToken, PasswordResetToken, RefreshToken


@celery_app.task(name="app.users.tasks.send_activation_email_task")
def send_activation_email_task(email: str, token: str) -> None:
    send_activation_email(email, token)


@celery_app.task(name="app.users.tasks.delete_expired_tokens")
def delete_expired_tokens() -> int:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        count = 0

        for model in (ActivationToken, PasswordResetToken, RefreshToken):
            expired = (
                db.query(model)
                .filter(model.expires_at < now)
                .all()
            )

            count += len(expired)

            for token in expired:
                db.delete(token)
                
        db.commit()

        return count

    finally:
        db.close()


@celery_app.task(name="app.users.tasks.send_reset_email_task")
def send_reset_email_task(email: str, token: str) -> None:
    send_reset_email(email, token)
