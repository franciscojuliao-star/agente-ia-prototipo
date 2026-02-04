"""
Dependencies de autenticação para FastAPI.
"""
import time
import uuid
from collections import defaultdict
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.jwt import verify_token
from app.config import get_settings
from app.database import get_db
from app.models import User, UserRole

settings = get_settings()
security = HTTPBearer()


class RateLimiter:
    """
    Rate limiter simples em memória.
    Em produção, use Redis para suporte a múltiplas instâncias.
    """

    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        """
        Verifica se o usuário pode fazer mais requisições.

        Args:
            user_id: ID do usuário

        Returns:
            True se permitido, False se rate limitado
        """
        now = time.time()
        minute_ago = now - 60

        # Remove requisições antigas
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id] if req_time > minute_ago
        ]

        if len(self.requests[user_id]) >= self.requests_per_minute:
            return False

        self.requests[user_id].append(now)
        return True


# Instância global do rate limiter
rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Dependency que extrai e valida o usuário atual do token JWT.

    Args:
        credentials: Credenciais do header Authorization
        db: Sessão do banco de dados

    Returns:
        Usuário autenticado

    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(credentials.credentials, token_type="access")
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    # Verifica se usuário está ativo
    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada ou aguardando aprovação",
        )

    return user


async def get_current_professor(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency que verifica se o usuário atual é professor.

    Args:
        current_user: Usuário autenticado

    Returns:
        Usuário professor

    Raises:
        HTTPException: Se usuário não for professor
    """
    if current_user.role != UserRole.PROFESSOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para professores",
        )
    return current_user


async def get_current_aluno(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency que verifica se o usuário atual é aluno.

    Args:
        current_user: Usuário autenticado

    Returns:
        Usuário aluno

    Raises:
        HTTPException: Se usuário não for aluno
    """
    if current_user.role != UserRole.ALUNO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para alunos",
        )
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency que verifica se o usuário atual é administrador.

    Args:
        current_user: Usuário autenticado

    Returns:
        Usuário administrador

    Raises:
        HTTPException: Se usuário não for administrador
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso permitido apenas para administradores",
        )
    return current_user


def check_rate_limit(user: User) -> None:
    """
    Verifica rate limit para o usuário.

    Args:
        user: Usuário a verificar

    Raises:
        HTTPException: Se rate limit excedido
    """
    if not rate_limiter.is_allowed(str(user.id)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit excedido. Máximo de {settings.rate_limit_per_minute} requisições por minuto.",
        )
