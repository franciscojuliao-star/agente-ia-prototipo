#!/bin/bash
set -e

echo "=== Iniciando AVA RAG Backend ==="

# Aguarda o PostgreSQL estar pronto
echo "Aguardando PostgreSQL..."
while ! python -c "from app.database import engine; engine.connect()" 2>/dev/null; do
    sleep 2
done
echo "PostgreSQL conectado!"

# Executa migração para adicionar campo ativo e criar admin
echo "Executando migração..."
python scripts/migrate_add_admin.py

echo "=== Iniciando servidor ==="
exec "$@"
