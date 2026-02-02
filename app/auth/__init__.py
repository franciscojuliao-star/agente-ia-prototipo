"""
Módulo de autenticação.
"""
from app.auth.jwt import create_access_token, create_refresh_token, verify_token
from app.auth.dependencies import (
    get_current_user,
    get_current_professor,
    get_current_aluno,
    RateLimiter,
)

__all__ = [
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "get_current_user",
    "get_current_professor",
    "get_current_aluno",
    "RateLimiter",
]
