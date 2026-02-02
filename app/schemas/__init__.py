"""
Schemas Pydantic para validação de dados.
"""
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
)
from app.schemas.material import (
    MaterialBase,
    MaterialCreate,
    MaterialResponse,
    VideoUpload,
    LinkUpload,
    TextoUpload,
)
from app.schemas.conteudo import (
    GerarQuizRequest,
    GerarResumoRequest,
    GerarFlashcardsRequest,
    ConteudoResponse,
    AprovarConteudoRequest,
    RejeitarConteudoRequest,
    RegenerarConteudoRequest,
    ResponderQuizRequest,
    TentativaResponse,
    BuscaSemanticaRequest,
    BuscaSemanticaResponse,
)

__all__ = [
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "MaterialBase",
    "MaterialCreate",
    "MaterialResponse",
    "VideoUpload",
    "LinkUpload",
    "TextoUpload",
    "GerarQuizRequest",
    "GerarResumoRequest",
    "GerarFlashcardsRequest",
    "ConteudoResponse",
    "AprovarConteudoRequest",
    "RejeitarConteudoRequest",
    "RegenerarConteudoRequest",
    "ResponderQuizRequest",
    "TentativaResponse",
    "BuscaSemanticaRequest",
    "BuscaSemanticaResponse",
]
