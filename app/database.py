"""
Configuração do banco de dados PostgreSQL com SQLAlchemy.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependency que fornece uma sessão do banco de dados.
    Garante fechamento da sessão após uso.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Inicializa o banco de dados criando todas as tabelas."""
    Base.metadata.create_all(bind=engine)
