"""
Utilitários JWT para autenticação.
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Contexto para hash de senhas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto plano corresponde ao hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Gera hash bcrypt da senha."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: uuid.UUID,
    email: str,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Cria token de acesso JWT.

    Args:
        user_id: ID do usuário
        email: Email do usuário
        role: Role do usuário (PROFESSOR/ALUNO)
        expires_delta: Tempo de expiração customizado

    Returns:
        Token JWT codificado
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token(user_id: uuid.UUID) -> str:
    """
    Cria refresh token JWT.

    Args:
        user_id: ID do usuário

    Returns:
        Refresh token JWT codificado
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def verify_token(token: str, token_type: str = "access") -> dict | None:
    """
    Verifica e decodifica um token JWT.

    Args:
        token: Token JWT a verificar
        token_type: Tipo esperado ('access' ou 'refresh')

    Returns:
        Payload do token se válido, None caso contrário
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
