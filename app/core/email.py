import smtplib
from users.email import EmailMessage
from app.core.config import settings


def send_email(to: str, subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        if settings.MAIL_STARTTLS:
            server.starttls()
        if settings.MAIL_USERNAME:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.send_message(msg)


def send_activation_email(to: str, token: str) -> None:
    link = f"{settings.FRONTEND_URL}/users/activate?token={token}"
    send_email(
        to=to,
        subject="Activate your account",
        body=(
            f"Welcome! Please activate your account within 24 hours:\n\n{link}\n\n"
            "If the link expires, you can request a new one."
        ),
    )
