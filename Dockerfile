# Backend Dockerfile - Otimizado para Servidor Xeon
FROM python:3.11-slim

WORKDIR /app

# Variáveis de ambiente para produção
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Criar usuário não-root (segurança)
RUN useradd --create-home --shell /bin/bash appuser

# Copiar requirements primeiro (cache de camadas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Criar diretórios necessários e ajustar permissões
RUN mkdir -p uploads chroma_db \
    && chown -R appuser:appuser /app

# Trocar para usuário não-root
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

# Expor porta
EXPOSE 8000

# Comando otimizado para Xeon (4 workers para aproveitar múltiplos cores)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
