from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.core.config import settings

_mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
)

_mailer = FastMail(_mail_config)


async def send_otp_email(email: str, otp: str) -> None:
    message = MessageSchema(
        subject="Password Reset OTP",
        recipients=[email],
        body=(
            f"Your OTP for password reset is: <strong>{otp}</strong><br>"
            f"It expires in {settings.OTP_EXPIRE_MINUTES} minutes.<br>"
            "Do not share this code with anyone."
        ),
        subtype=MessageType.html,
    )
    await _mailer.send_message(message)


async def send_invite_email(email: str, invite_link: str) -> None:
    message = MessageSchema(
        subject="You're invited to join the Academic Portal",
        recipients=[email],
        body=(
            f"You have been invited as a Lecturer.<br>"
            f"Click the link to complete registration: <a href='{invite_link}'>{invite_link}</a><br>"
            "This link expires in 48 hours."
        ),
        subtype=MessageType.html,
    )
    await _mailer.send_message(message)
