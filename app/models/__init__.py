"""
Modelos SQLAlchemy do sistema.
"""
from app.models.user import User, UserRole
from app.models.material import Material, TipoMaterial
from app.models.conteudo_gerado import (
    ConteudoGerado,
    TipoConteudo,
    StatusConteudo,
    TentativaAluno,
)

__all__ = [
    "User",
    "UserRole",
    "Material",
    "TipoMaterial",
    "ConteudoGerado",
    "TipoConteudo",
    "StatusConteudo",
    "TentativaAluno",
]
