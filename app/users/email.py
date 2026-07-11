from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=bool(settings.MAIL_USERNAME),
)
fm = FastMail(conf)


async def send_activation_email(email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/users/activate?token={token}"
    await fm.send_message(
        MessageSchema(
            subject="Activate your account",
            recipients=[email],
            body=f"Activate your account within 24h: {link}",
            subtype=MessageType.plain,
        )
    )


async def send_reset_email(email: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/users/reset-password?token={token}"
    await fm.send_message(
        MessageSchema(
            subject="Reset your password",
            recipients=[email],
            body=f"Reset your password: {link}",
            subtype=MessageType.plain,
        )
    )
