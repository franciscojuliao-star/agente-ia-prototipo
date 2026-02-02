"""
Schemas de usuário e autenticação.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema para criação de usuário."""
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=100)
    nome: str = Field(..., min_length=2, max_length=255)
    role: Literal["PROFESSOR", "ALUNO"] = "ALUNO"


class UserLogin(BaseModel):
    """Schema para login."""
    email: EmailStr
    senha: str


class UserResponse(BaseModel):
    """Schema de resposta com dados do usuário."""
    id: uuid.UUID
    email: str
    nome: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema de token JWT."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema de dados extraídos do token."""
    user_id: uuid.UUID | None = None
    email: str | None = None
    role: str | None = None
