"""
Modelo de usuário do sistema.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    """Tipos de usuário no sistema."""
    ADMIN = "ADMIN"
    PROFESSOR = "PROFESSOR"
    ALUNO = "ALUNO"


class User(Base):
    """Modelo de usuário (professor ou aluno)."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.ALUNO,
    )
    ativo: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,  # Usuários precisam ser aprovados pelo admin
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relacionamentos
    materiais: Mapped[list["Material"]] = relationship(
        "Material",
        back_populates="professor",
        cascade="all, delete-orphan",
    )
    conteudos_gerados: Mapped[list["ConteudoGerado"]] = relationship(
        "ConteudoGerado",
        back_populates="professor",
        cascade="all, delete-orphan",
    )
    tentativas: Mapped[list["TentativaAluno"]] = relationship(
        "TentativaAluno",
        back_populates="aluno",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role}, ativo={self.ativo})>"
