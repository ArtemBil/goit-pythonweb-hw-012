from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from .auth import auth_service
from ..conf.config import app_settings

"""Email service for sending verification and other transactional emails."""

conf = ConnectionConfig(
    MAIL_USERNAME = app_settings.MAIL_USERNAME,
    MAIL_PASSWORD = app_settings.MAIL_PASSWORD,
    MAIL_FROM = app_settings.MAIL_FROM,
    MAIL_PORT = app_settings.MAIL_PORT,
    MAIL_SERVER = app_settings.MAIL_SERVER,
    MAIL_FROM_NAME = app_settings.MAIL_FROM_NAME,
    MAIL_STARTTLS = app_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = app_settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = app_settings.USE_CREDENTIALS,
    VALIDATE_CERTS = app_settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates"
)

async def send_email(email: EmailStr, username: str, host: str):
    """Send a verification email containing a confirmation link.

    Args:
        email: Recipient address.
        username: Recipient user name for personalization.
        host: Base URL of the API used to build confirmation links.
    """
    try:
        token_verification = await auth_service.create_access_token({"sub": email})

        message = MessageSchema(
            subject="Verify your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification
            },
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

async def send_password_reset_email(email: EmailStr, username: str, host: str, reset_token: str):
    """Send a password reset email with a tokenized link.

    Args:
        email: Recipient address.
        username: Recipient user name for personalization.
        host: Base URL of the API used to build reset link.
        reset_token: Pre-generated reset token for the user.
    """
    try:
        message = MessageSchema(
            subject="Reset your password",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": reset_token
            },
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        # Reuse verify template for simplicity if no reset template provided
        await fm.send_message(message, template_name="reset_password_email.html")
    except ConnectionErrors as err:
        print(err)