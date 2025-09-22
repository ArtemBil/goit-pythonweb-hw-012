"""Rate limiting configuration using SlowAPI.

Exposes a `limiter` instance with client IP based key function.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)