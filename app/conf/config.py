from pydantic import EmailStr
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pydantic_settings import BaseSettings, SettingsConfigDict

"""Application configuration and database session factory."""

class Settings(BaseSettings):
    """Pydantic settings loaded from environment variables (.env)."""
    DATABASE_URL: str
    APP_NAME: str
    SECRET_KEY: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    REDIS_URL: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env")

app_settings = Settings()

engine = create_engine(app_settings.DATABASE_URL)
Session = sessionmaker(engine)
session = Session()

def get_db():
    """Yield a request-scoped database session."""
    db = session
    try:
        yield db
    finally:
        db.close()

