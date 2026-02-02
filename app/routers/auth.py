"""
Router de autenticação.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, UserRole
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post(
    "/registrar",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
)
async def registrar(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Registra um novo usuário no sistema.

    - **email**: Email único do usuário
    - **senha**: Senha com mínimo de 6 caracteres
    - **nome**: Nome completo
    - **role**: PROFESSOR ou ALUNO
    """
    # Verifica se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado",
        )

    # Cria novo usuário
    user = User(
        email=user_data.email,
        senha_hash=get_password_hash(user_data.senha),
        nome=user_data.nome,
        role=UserRole(user_data.role),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Autenticar usuário",
)
async def login(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Autentica usuário e retorna tokens JWT.

    - **email**: Email do usuário
    - **senha**: Senha do usuário

    Retorna access_token e refresh_token.
    """
    # Busca usuário
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not verify_password(credentials.senha, user.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
    refresh_token = create_refresh_token(user_id=user.id)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Renovar tokens",
)
async def refresh_token(
    refresh_token: str,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Renova tokens usando refresh_token válido.

    - **refresh_token**: Token de refresh válido

    Retorna novos access_token e refresh_token.
    """
    # Verifica refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado",
        )

    # Busca usuário
    user_id = uuid.UUID(payload["sub"])
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    # Gera novos tokens
    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
    new_refresh_token = create_refresh_token(user_id=user.id)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obter usuário atual",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Retorna dados do usuário autenticado.
    """
    return current_user
