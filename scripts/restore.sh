#!/bin/bash
# =============================================================================
# restore.sh - Restauration de la base de données Odoo
# =============================================================================
# Usage :
#   ./scripts/restore.sh backups/db_20250714_120000.dump
# =============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <fichier_backup.dump>"
    echo ""
    echo "Backups disponibles :"
    ls -1 "./backups/"*.dump 2>/dev/null || echo "   Aucun backup trouvé."
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Fichier introuvable : $BACKUP_FILE"
    exit 1
fi

echo "⏳ Restauration de $BACKUP_FILE..."
echo "⚠️  Attention : la base de données actuelle sera REMPLACÉE."
read -p "Continuer ? (o/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "❌ Restauration annulée."
    exit 1
fi

docker compose exec -T db pg_restore -U odoo -d postgres --clean \
    < "$BACKUP_FILE"

echo "✅ Base restaurée."
docker compose restart odoo
echo "✅ Odoo redémarré."
