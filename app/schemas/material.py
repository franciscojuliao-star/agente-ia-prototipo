"""
Schemas de material didático.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class MaterialBase(BaseModel):
    """Schema base de material."""
    disciplina: str = Field(..., min_length=2, max_length=255)
    titulo: str = Field(..., min_length=2, max_length=500)


class MaterialCreate(MaterialBase):
    """Schema para criação de material via texto."""
    tipo: Literal["PDF", "VIDEO", "LINK", "TEXTO"]
    conteudo_original: str | None = None
    url: str | None = None


class VideoUpload(MaterialBase):
    """Schema para upload de vídeo do YouTube."""
    url: HttpUrl


class LinkUpload(MaterialBase):
    """Schema para upload de link/webpage."""
    url: HttpUrl


class TextoUpload(MaterialBase):
    """Schema para upload de texto puro."""
    texto: str = Field(..., min_length=10)


class MaterialResponse(BaseModel):
    """Schema de resposta de material."""
    id: uuid.UUID
    professor_id: uuid.UUID
    disciplina: str
    titulo: str
    tipo: str
    num_chunks: int
    url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MaterialListResponse(BaseModel):
    """Schema de lista de materiais."""
    materiais: list[MaterialResponse]
    total: int
