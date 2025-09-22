from typing import Optional, Literal

from fastapi import HTTPException, status
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError
from ..conf.config import app_settings, get_db
from datetime import datetime, timedelta, timezone
from ..repositories.auth import auth_repository
from sqlalchemy.orm import Session
from .cache import cache_service

"""
Authentication service handles password hashing/verification, JWT creation and
validation, and current-user resolution with Redis-backed caching.
"""

REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ACCESS_TOKEN_EXPIRE_MINUTES = 15

class AuthService:
    pwd_context = CryptContext(schemes=["bcrypt"])
    oauth2_schema = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

    def verify_password(self, plain_password: str, hashed_password: str):
        return self.pwd_context.verify(plain_password, hashed_password)

    def hash_password(self, password: str):
        return self.pwd_context.hash(password)

    async def create_token(self, payload: dict, expires_delta: timedelta | float, token_type: Optional[Literal["access", "refresh", "reset"]]):
        to_encode = payload.copy()
        now = datetime.now(timezone.utc)
        if isinstance(expires_delta, (int, float)):
            expires_delta = timedelta(minutes=expires_delta)
        expire = now + expires_delta
        if token_type:
            to_encode.update({"exp": expire, "iat": now, "token_type": token_type})
        else:
            to_encode.update({"exp": expire, "iat": now})
        encoded_jwt = jwt.encode(to_encode, app_settings.SECRET_KEY)

        return encoded_jwt

    async def create_access_token(self, payload: dict, expires_delta: float = 15):
        if expires_delta:
            access_token = await self.create_token(payload, expires_delta, "access")
        else:
            access_token = await self.create_token(
                payload, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access"
            )
        return access_token

    async def create_refresh_token(self, payload: dict, expires_delta: Optional[float] = None):
        if expires_delta:
            refresh_token = await self.create_token(payload, expires_delta, "refresh")
        else:
            refresh_token = await self.create_token(payload, timedelta(days=REFRESH_TOKEN_EXPIRE_MINUTES), "refresh")

        return refresh_token

    async def create_reset_token(self, payload: dict, expires_minutes: int = 30):
        return await self.create_token(payload, timedelta(minutes=expires_minutes), "reset")

    async def get_current_user(self, token: str = Depends(oauth2_schema), db: Session = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, app_settings.SECRET_KEY)
            email: str = payload.get("sub")
            token_type: str = payload.get("token_type")

            if email is None or token_type != "access":
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        # Try cache by token first
        cached_user = await cache_service.get_user_by_token(token)
        if cached_user:
            return cached_user

        user = await auth_repository.get_user_by_email(email, db)
        if user is None:
            raise credentials_exception

        # Cache user for the duration of access token
        await cache_service.set_user_for_token(token, user)
        return user

    def verify_refresh_token(self, refresh_token: str, db: Session):
        try:
            payload = jwt.decode(refresh_token, app_settings.SECRET_KEY)
            username: str = payload.get("sub")
            token_type: str = payload.get("token_type")

            if username is None or token_type != "refresh":
                return None

            user = auth_repository.get_user_refresh_token(username, refresh_token, db)

            return user
        except JWTError:
            return None

    async def get_user_by_email_token(self, token: str):
        try:
            payload = jwt.decode(token, app_settings.SECRET_KEY)

            email = payload.get("sub")
            return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials from email",
                headers={"WWW-Authenticate": "Bearer"},
            )

auth_service = AuthService()