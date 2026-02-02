#!/bin/bash
# Configura limpeza automática semanal
# Execute com: sudo ./scripts/setup-cron.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CLEANUP_SCRIPT="$SCRIPT_DIR/cleanup.sh"

# Tornar executável
chmod +x "$CLEANUP_SCRIPT"

# Adicionar ao cron (todo domingo às 3h da manhã)
(crontab -l 2>/dev/null | grep -v "cleanup.sh"; echo "0 3 * * 0 $CLEANUP_SCRIPT >> /var/log/ava-cleanup.log 2>&1") | crontab -

echo "✅ Limpeza automática configurada!"
echo "   Executa todo domingo às 3h da manhã"
echo "   Log em: /var/log/ava-cleanup.log"
echo ""
echo "Para executar manualmente: $CLEANUP_SCRIPT"
