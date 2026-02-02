#!/bin/bash
# Script de limpeza automática para o AVA RAG
# Execute com: ./scripts/cleanup.sh

echo "🧹 Limpeza do AVA RAG - Servidor Ubuntu"
echo "========================================"

# Mostrar espaço atual
echo ""
echo "📊 Espaço atual:"
df -h / | tail -1

# Limpar containers parados
echo ""
echo "🗑️  Removendo containers parados..."
docker container prune -f

# Limpar imagens não utilizadas
echo ""
echo "🗑️  Removendo imagens não utilizadas..."
docker image prune -f

# Limpar volumes órfãos (CUIDADO: não remove volumes nomeados)
echo ""
echo "🗑️  Removendo volumes órfãos..."
docker volume prune -f

# Limpar cache de build
echo ""
echo "🗑️  Removendo cache de build..."
docker builder prune -f

# Limpar logs antigos dos containers (mantém últimos 10MB)
echo ""
echo "🗑️  Truncando logs grandes..."
for log in $(find /var/lib/docker/containers/ -name "*.log" 2>/dev/null); do
    if [ -f "$log" ]; then
        sudo truncate -s 10M "$log" 2>/dev/null
    fi
done

# Mostrar espaço liberado
echo ""
echo "📊 Espaço após limpeza:"
df -h / | tail -1

echo ""
echo "✅ Limpeza concluída!"