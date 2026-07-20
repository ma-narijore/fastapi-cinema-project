from datetime import datetime, timezone
from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.email_service import send_activation_email
from app.users.models import ActivationToken


@celery_app.task(name="app.users.tasks.send_activation_email_task")
def send_activation_email_task(email: str, token: str) -> None:
    send_activation_email(email, token)


@celery_app.task(name="app.users.tasks.delete_expired_activation_tokens")
def delete_expired_activation_tokens() -> int:
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        expired = (
            db.query(ActivationToken)
            .filter(ActivationToken.expires_at < now)
            .all()
        )

        count = len(expired)

        for token in expired:
            db.delete(token)

        db.commit()

        return count

    finally:
        db.close()
