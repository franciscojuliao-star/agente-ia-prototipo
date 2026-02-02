"""
Modelo de material didático do sistema.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TipoMaterial(str, enum.Enum):
    """Tipos de material suportados."""
    PDF = "PDF"
    VIDEO = "VIDEO"
    LINK = "LINK"
    TEXTO = "TEXTO"


class Material(Base):
    """Modelo de material didático enviado pelo professor."""

    __tablename__ = "materiais"

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
    disciplina: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    titulo: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo: Mapped[TipoMaterial] = mapped_column(
        Enum(TipoMaterial),
        nullable=False,
    )
    conteudo_original: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    arquivo_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    num_chunks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relacionamentos
    professor: Mapped["User"] = relationship("User", back_populates="materiais")

    def __repr__(self) -> str:
        return f"<Material(id={self.id}, titulo={self.titulo}, tipo={self.tipo})>"
