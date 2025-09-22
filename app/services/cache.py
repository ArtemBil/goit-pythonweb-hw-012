from typing import Optional
import json
from redis.asyncio import Redis
from ..conf.config import app_settings

"""Redis-backed caching utilities for authenticated user data."""

class CacheService:
    """Cache service for storing and retrieving current user by access token."""
    def __init__(self) -> None:
        self.client: Redis = Redis.from_url(app_settings.REDIS_URL, decode_responses=True)
        self.prefix = "auth:user:token:"
        self.ttl_seconds = 15 * 60
        # Password reset token storage (single-use)
        self.reset_prefix = "auth:reset:token:"
        self.reset_ttl_seconds = 30 * 60

    async def set_user_for_token(self, token: str, user) -> None:
        """Cache minimal user payload under the given access token."""
        data = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "avatar": user.avatar,
            "role": getattr(user, "role", "user"),
            "confirmed": bool(user.confirmed),
        }
        await self.client.setex(self.prefix + token, self.ttl_seconds, json.dumps(data))

    async def get_user_by_token(self, token: str) -> Optional[object]:
        """Retrieve cached user by access token or None if missing/expired."""
        raw = await self.client.get(self.prefix + token)
        if not raw:
            return None
        data = json.loads(raw)
        # Return a simple object with attributes to mimic ORM user for read-only usage
        return type("CachedUser", (), data)

    async def set_password_reset_token(self, token: str, email: str) -> None:
        """Store a single-use password reset token mapped to user's email.

        The token will automatically expire after `reset_ttl_seconds`.
        """
        await self.client.setex(self.reset_prefix + token, self.reset_ttl_seconds, email)

    async def pop_email_by_reset_token(self, token: str) -> Optional[str]:
        """Atomically fetch and invalidate a reset token, returning the email.

        Returns None if the token is missing or expired. This enforces single-use tokens.
        """
        key = self.reset_prefix + token
        # Use a Lua script to get-and-delete atomically
        script = """
        local val = redis.call('GET', KEYS[1])
        if val then
            redis.call('DEL', KEYS[1])
        end
        return val
        """
        try:
            email = await self.client.eval(script, 1, key)
        except Exception:
            # Fallback if EVAL is disabled: best-effort get/del
            email = await self.client.get(key)
            if email:
                await self.client.delete(key)
        return email

cache_service = CacheService() 