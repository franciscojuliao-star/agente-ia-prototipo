"""
Schemas de conteúdo gerado.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GerarQuizRequest(BaseModel):
    """Schema para solicitação de geração de quiz."""
    topico: str = Field(..., min_length=3, max_length=500)
    disciplina: str = Field(..., min_length=2, max_length=255)
    num_questoes: int = Field(default=5, ge=1, le=20)
    dificuldade: Literal["facil", "medio", "dificil"] = "medio"
    material_ids: list[uuid.UUID] | None = None


class GerarResumoRequest(BaseModel):
    """Schema para solicitação de geração de resumo."""
    topico: str = Field(..., min_length=3, max_length=500)
    disciplina: str = Field(..., min_length=2, max_length=255)
    tamanho: Literal["curto", "medio", "longo"] = "medio"
    material_ids: list[uuid.UUID] | None = None


class GerarFlashcardsRequest(BaseModel):
    """Schema para solicitação de geração de flashcards."""
    topico: str = Field(..., min_length=3, max_length=500)
    disciplina: str = Field(..., min_length=2, max_length=255)
    num_cards: int = Field(default=10, ge=1, le=50)
    material_ids: list[uuid.UUID] | None = None


class ConteudoResponse(BaseModel):
    """Schema de resposta de conteúdo gerado."""
    id: uuid.UUID
    professor_id: uuid.UUID
    tipo: str
    topico: str
    disciplina: str
    conteudo_json: dict
    status: str
    material_fonte_ids: list[uuid.UUID]
    criado_em: datetime
    aprovado_em: datetime | None = None
    modificacoes_professor: dict | None = None
    motivo_rejeicao: str | None = None
    watermark: str | None = None

    model_config = {"from_attributes": True}


class ConteudoListResponse(BaseModel):
    """Schema de lista de conteúdos."""
    conteudos: list[ConteudoResponse]
    total: int


class AprovarConteudoRequest(BaseModel):
    """Schema para aprovação de conteúdo."""
    modificacoes: dict | None = None


class RejeitarConteudoRequest(BaseModel):
    """Schema para rejeição de conteúdo."""
    motivo: str = Field(..., min_length=10, max_length=1000)


class RegenerarConteudoRequest(BaseModel):
    """Schema para regeneração de conteúdo."""
    ajustes: str = Field(..., min_length=10, max_length=1000)


class ResponderQuizRequest(BaseModel):
    """Schema para resposta de quiz do aluno."""
    respostas: dict[str, str] = Field(
        ...,
        description="Dicionário com índice da questão como chave e alternativa como valor",
    )


class TentativaResponse(BaseModel):
    """Schema de resposta de tentativa."""
    id: uuid.UUID
    aluno_id: uuid.UUID
    conteudo_id: uuid.UUID
    respostas_json: dict
    pontuacao: float
    created_at: datetime
    detalhes: dict | None = None

    model_config = {"from_attributes": True}


class TentativaListResponse(BaseModel):
    """Schema de lista de tentativas."""
    tentativas: list[TentativaResponse]
    total: int


class BuscaSemanticaRequest(BaseModel):
    """Schema para busca semântica."""
    disciplina: str = Field(..., min_length=2, max_length=255)
    pergunta: str = Field(..., min_length=5, max_length=1000)


class BuscaSemanticaResponse(BaseModel):
    """Schema de resposta de busca semântica."""
    trechos: list[dict]
    pergunta: str
    disciplina: str


class DisciplinaResponse(BaseModel):
    """Schema de disciplina."""
    nome: str
    num_conteudos: int


class DisciplinasListResponse(BaseModel):
    """Schema de lista de disciplinas."""
    disciplinas: list[DisciplinaResponse]
