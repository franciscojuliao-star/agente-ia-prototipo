"""
Configuração centralizada da aplicação usando Pydantic Settings.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Configuration
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"  # Modelo menor e mais rápido
    ollama_timeout: int = 300  # 5 minutos para modelos locais

    # Embedding Configuration
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"

    # Database Configuration
    database_url: str = "postgresql://ava_user:senha123@localhost:5432/ava_db"

    # JWT Configuration
    secret_key: str = "sua-chave-secreta-jwt-aqui-mude-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Application Settings
    max_upload_size_mb: int = 50
    rate_limit_per_minute: int = 10
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200

    @property
    def max_upload_size_bytes(self) -> int:
        """Retorna tamanho máximo de upload em bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
