#!/bin/bash
# =============================================================================
# backup.sh - Sauvegarde de la base de données et du filestore Odoo
# =============================================================================
# Usage :
#   ./scripts/backup.sh              # Backup horodaté dans ./backups/
#   ./scripts/backup.sh prod         # Backup avec suffixe personnalisé
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_DIR/backups"

SUFFIX="${1:-$(date +%Y%m%d_%H%M%S)}"
mkdir -p "$BACKUP_DIR"

echo "⏳ Sauvegarde en cours..."

# 1. Backup de la base PostgreSQL
docker compose exec -T db pg_dump -U odoo -d postgres -F c \
    > "$BACKUP_DIR/db_$SUFFIX.dump" 2>/dev/null

# 2. Backup du filestore Odoo (pièces jointes)
docker compose exec -T odoo tar czf - /var/lib/odoo/filestore \
    > "$BACKUP_DIR/filestore_$SUFFIX.tar.gz" 2>/dev/null

echo "✅ Sauvegarde terminée :"
ls -lh "$BACKUP_DIR/db_$SUFFIX.dump" "$BACKUP_DIR/filestore_$SUFFIX.tar.gz"
