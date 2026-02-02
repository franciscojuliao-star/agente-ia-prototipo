"""
Modelos de conteúdo gerado e tentativas de alunos.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import ARRAY, JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoConteudo(str, enum.Enum):
    """Tipos de conteúdo que podem ser gerados."""
    QUIZ = "QUIZ"
    RESUMO = "RESUMO"
    FLASHCARD = "FLASHCARD"


class StatusConteudo(str, enum.Enum):
    """Status do conteúdo gerado."""
    AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    APROVADO = "APROVADO"
    REJEITADO = "REJEITADO"


class ConteudoGerado(Base):
    """Modelo de conteúdo gerado pela IA."""

    __tablename__ = "conteudos_gerados"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    professor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tipo: Mapped[TipoConteudo] = mapped_column(
        Enum(TipoConteudo),
        nullable=False,
    )
    conteudo_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[StatusConteudo] = mapped_column(
        Enum(StatusConteudo),
        nullable=False,
        default=StatusConteudo.AGUARDANDO_APROVACAO,
        index=True,
    )
    material_fonte_ids: Mapped[list[str]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        default=list,
    )
    topico: Mapped[str] = mapped_column(String(500), nullable=False)
    disciplina: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    aprovado_em: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    modificacoes_professor: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    motivo_rejeicao: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Relacionamentos
    professor: Mapped["User"] = relationship(
        "User",
        back_populates="conteudos_gerados",
    )
    tentativas: Mapped[list["TentativaAluno"]] = relationship(
        "TentativaAluno",
        back_populates="conteudo",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ConteudoGerado(id={self.id}, tipo={self.tipo}, status={self.status})>"


class TentativaAluno(Base):
    """Modelo de tentativa de resposta do aluno."""

    __tablename__ = "tentativas_alunos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    aluno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conteudo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conteudos_gerados.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    respostas_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    pontuacao: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    aluno: Mapped["User"] = relationship("User", back_populates="tentativas")
    conteudo: Mapped["ConteudoGerado"] = relationship(
        "ConteudoGerado",
        back_populates="tentativas",
    )

    def __repr__(self) -> str:
        return f"<TentativaAluno(id={self.id}, pontuacao={self.pontuacao})>"
