#!/usr/bin/env bash
# =============================================================================
# Installation d'ArgoCD sur k3s (à exécuter SUR le nœud k3s, où kubectl pointe
# vers le cluster). Démarre : argocd namespace, contrôleur, serveur, UI.
# =============================================================================
set -euo pipefail

echo "[ARGOCD] Création du namespace argocd..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

echo "[ARGOCD] Installation d'ArgoCD (manifests officiels stable)..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo "[ARGOCD] Attente du serveur (peut prendre 1-2 min)..."
kubectl -n argocd rollout status deployment/argocd-server --timeout=300s

echo ""
echo "[ARGOCD] ✅ Installé. Mot de passe admin initial :"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""
echo "Accès UI : kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "          puis http://localhost:8080 (admin / <mot de passe ci-dessus>)"
