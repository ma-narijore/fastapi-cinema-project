from celery import Celery
from celery.schedules import crontab
from app.core.config import settings


celery_app = Celery(
    "cinema",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.users.tasks"],
)

celery_app.conf.beat_schedule = {
    "delete-expired-tokens": {
        "task": "app.users.tasks.delete_expired_tokens",
        "schedule": crontab(minute=0, hour="*"), # hourly cleanup
        # "schedule": timedelta(seconds=10),
    },
}

celery_app.conf.timezone = "UTC"
