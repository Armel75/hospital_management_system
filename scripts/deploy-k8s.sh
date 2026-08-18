#!/bin/bash
# =============================================================================
# deploy-k8s.sh — Déploiement automatisé sur k3s (Ubuntu)
# =============================================================================
# Usage :
#   chmod +x scripts/deploy-k8s.sh
#   ./scripts/deploy-k8s.sh
#
# Prérequis (sur le serveur Ubuntu) :
#   - k3s installé
#   - image hospital-odoo:1.0.0 importée dans k3s
#   - repo cloné et secrets configurés
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NAMESPACE="hospital"

echo "╔══════════════════════════════════════════════════╗"
echo "║   Déploiement Hôpital sur k3s                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Vérifier k3s ────────────────────────────────────────────────────────
echo "[1/6] Vérification de k3s..."
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl non trouvé. Installez k3s :"
    echo "    curl -sfL https://get.k3s.io | sh -"
    exit 1
fi

if ! kubectl get nodes &> /dev/null; then
    echo "❌ k3s ne répond pas. Vérifiez l'installation :"
    echo "    sudo systemctl status k3s"
    exit 1
fi
echo "✅ k3s OK"

# ── 2. Vérifier l'image ────────────────────────────────────────────────────
echo "[2/6] Vérification de l'image hospital-odoo..."
if ! sudo k3s ctr images list | grep -q "hospital-odoo"; then
    echo "⚠️  Image hospital-odoo non trouvée dans k3s."
    echo "    Importez-la d'abord :"
    echo "    sudo k3s ctr images import /chemin/vers/hospital-odoo-1.0.0.tar"
    exit 1
fi
echo "✅ Image hospital-odoo trouvée"

# ── 3. Vérifier les secrets ────────────────────────────────────────────────
echo "[3/6] Vérification des secrets..."
if grep -q "CHANGE_ME" "$PROJECT_DIR/k8s/base/secrets.yaml"; then
    echo "❌ Placeholders CHANGE_ME trouvés dans k8s/base/secrets.yaml"
    echo "    Éditez ce fichier et remplacez les mots de passe avant de déployer."
    exit 1
fi
echo "✅ Secrets configurés"

# ── 4. Appliquer les manifests ─────────────────────────────────────────────
echo "[4/6] Déploiement des manifests Kubernetes..."
kubectl apply -k "$PROJECT_DIR/k8s/"
echo "✅ Manifests appliqués"

# ── 5. Attendre les pods ───────────────────────────────────────────────────
echo "[5/6] Attente du démarrage des pods (timeout 300s)..."
echo ""
kubectl rollout status deployment/odoo -n "$NAMESPACE" --timeout=300s
kubectl rollout status statefulset/db -n "$NAMESPACE" --timeout=300s
echo "✅ Pods démarrés"

# ── 6. Vérification finale ─────────────────────────────────────────────────
echo "[6/6] Vérification finale..."
echo ""
kubectl get pods,svc,ingress,statefulset -n "$NAMESPACE"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║   ✅ Déploiement terminé !                       ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "Accès :"
echo "  - Depuis le serveur : curl -I http://localhost/web/health"
echo "  - Port-forward      : kubectl port-forward -n $NAMESPACE svc/odoo 8069:8069"
echo "  - Logs Odoo         : kubectl logs -n $NAMESPACE -f deployment/odoo"
echo "  - Logs PostgreSQL   : kubectl logs -n $NAMESPACE -f statefulset/db"
echo ""
