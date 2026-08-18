# 🚀 Guide de déploiement — Hôpital sur k3s

> **Durée estimée** : 10–15 min (1er déploiement)  
> **Prérequis** : un nœud k3s opérationnel, Docker sur la machine de build, `kubectl` configuré.

---

## ⚠️ ÉTAPE 0 — Remplacer les placeholders (SINON ÉCHEC)

Avant TOUTE commande, remplace les `CHANGE_ME` dans ces fichiers :

| Fichier | Quoi remplacer | Par quoi |
|---|---|---|
| `k8s/base/secrets.yaml` | `POSTGRES_PASSWORD` | Mot de passe fort pour PostgreSQL |
| `k8s/base/secrets.yaml` | `ADMIN_PASSWORD` | Mot de passe master Odoo (clair ou hash pbkdf2) |
| `k8s/overlays/staging/kustomization.yaml` | `ghcr.io/CHANGE_ME/hospital-odoo` | Ton repo GHCR (ex: `ghcr.io/mon-org/hospital-odoo`) |
| `k8s/overlays/production/kustomization.yaml` | `ghcr.io/CHANGE_ME/hospital-odoo` | Idem |
| `argocd/project.yaml` | `https://github.com/CHANGE_ME/...` | URL de TON repo GitHub |
| `argocd/app-of-apps.yaml` | `https://github.com/CHANGE_ME/...` | Idem |
| `argocd/apps/hospital-staging.yaml` | `https://github.com/CHANGE_ME/...` | Idem |
| `argocd/apps/hospital-production.yaml` | `https://github.com/CHANGE_ME/...` | Idem |

> 💡 **Astuce** : si tu déploies sans GHCR (images locales k3s), ignore les overlays
> pour l'instant et utilise `kubectl apply -k k8s/` directement.

---

## ÉTAPE 1 — Sur la machine de build (où se trouve le code)

### 1.1 Construire l'image

```bash
docker build -t hospital-odoo:1.0.0 .
```

### 1.2 Transférer l'image sur le nœud k3s

**Si tu buildes SUR le nœud k3s** (même machine) :

```bash
# Importer directement dans k3s
docker save hospital-odoo:1.0.0 | sudo k3s ctr images import -
```

**Si tu buildes sur une AUTRE machine** (ton PC Windows) :

```bash
# 1. Sauvegarder l'image
docker save hospital-odoo:1.0.0 > hospital-odoo-1.0.0.tar

# 2. Transférer sur le nœud k3s (scp, USB, etc.)
scp hospital-odoo-1.0.0.tar user@k3s-node:/tmp/

# 3. Sur le nœud k3s, importer :
sudo k3s ctr images import /tmp/hospital-odoo-1.0.0.tar
```

---

## ÉTAPE 2 — Sur le nœud k3s (où kubectl pointe vers le cluster)

### 2.1 Vérifier que le cluster répond

```bash
kubectl get nodes
# Doit afficher ton nœud en Ready
```

### 2.2 Créer le secret d'image (si tu utilises GHCR — sinon passer)

```bash
kubectl create secret docker-registry ghcr-pull \
  --docker-server=ghcr.io \
  --docker-username=TON_GITHUB_USER \
  --docker-password=TON_GITHUB_TOKEN \
  -n hospital
```

> Si tu n'utilises pas GHCR (image locale importée), SAUTE cette étape.

### 2.3 Déployer

**Option A — Déploiement simple (image locale, sans GHCR)** :

```bash
# Déploie la base (namespace hospital)
kubectl apply -k k8s/
```

**Option B — Déploiement staging (avec GHCR)** :

```bash
kubectl apply -k k8s/overlays/staging
```

**Option C — Déploiement production (avec GHCR)** :

```bash
kubectl apply -k k8s/overlays/production
```

---

## ÉTAPE 3 — Vérifications post-déploiement

### 3.1 Attendre que tous les pods soient Ready

```bash
kubectl get pods,svc,ingress,statefulset -n hospital
# ou pour staging :
kubectl get pods,svc,ingress,statefulset -n hospital-staging
```

Tu dois voir :
- `pod/odoo-...` → `1/1 Running`
- `pod/db-0` → `1/1 Running`
- `statefulset/db` → `1/1`

> ⏱️ Le 1er démarrage peut prendre 30–60s (Odoo crée la base si elle n'existe pas).

### 3.2 Voir les logs en direct

```bash
# Odoo
kubectl logs -n hospital -f deployment/odoo

# PostgreSQL
kubectl logs -n hospital -f statefulset/db
```

### 3.3 Tester l'accès

```bash
# Depuis le nœud k3s (via Ingress Traefik)
curl -I http://localhost/web/health
# Doit retourner HTTP 200

# Ou ouvrir dans le navigateur (remplace <IP> par l'IP du nœud)
# http://<IP-DU-NOEUD>
```

### 3.4 Port-forward (si pas d'Ingress externe)

```bash
kubectl port-forward -n hospital svc/odoo 8169:8169
# Puis ouvrir http://localhost:8169 sur ta machine
```

---

## ÉTAPE 4 — Première connexion Odoo

1. Ouvrir `http://<IP-DU-NOEUD>`
2. Si c'est la 1ère installation, Odoo affiche l'écran de création de base :
   - **Master Password** : le `ADMIN_PASSWORD` que tu as mis dans `secrets.yaml`
   - Créer ta base de données
3. Installer les modules dans l'ordre :
   - `care_center_base`
   - `care_center_consultation`
   - `care_center_appointment`
   - `care_center_pharmacy`
   - `care_center_billing`

---

## 🔄 Mise à jour (nouvelle version)

```bash
# 1. Rebuild
docker build -t hospital-odoo:1.0.1 .

# 2. Réimporter dans k3s
docker save hospital-odoo:1.0.1 | sudo k3s ctr images import -

# 3. Forcer le redémarrage du pod (si imagePullPolicy: IfNotPresent)
kubectl rollout restart deployment/odoo -n hospital

# 4. Vérifier
kubectl rollout status deployment/odoo -n hospital
```

---

## 🆘 Dépannage rapide

| Symptôme | Cause probable | Solution |
|---|---|---|
| `CrashLoopBackOff` sur odoo | `DuplicateOptionError` (config Odoo) | Vérifie que `odoo-deployment.yaml` utilise bien `sed` pour nettoyer la config |
| `CrashLoopBackOff` sur odoo | Mauvais mot de passe DB | Vérifie `POSTGRES_PASSWORD` dans `secrets.yaml` |
| Pod odoo `Pending` | PVC non provisionné | Vérifie `storageClassName: local-path` existe : `kubectl get sc` |
| `ImagePullBackOff` | Image non trouvée | Vérifie l'image est importée : `sudo k3s ctr images list \| grep hospital` |
| `ErrImagePull` | GHCR privé sans secret | Crée le `secret docker-registry ghcr-pull` |
| Pas d'accès HTTP | Ingress non configuré | Utilise `kubectl port-forward` en attendant |
| PostgreSQL refuse | DB pas encore prête | Attends 10–20s, le `wait-for-psql.py` retry automatiquement |

---

## ☸️ GitOps (optionnel — après le 1er déploiage manuel)

Si le déploiage manuel fonctionne, tu peux activer ArgoCD :

```bash
make argocd:install    # ou bash argocd/install.sh
make argocd:password   # récupère le mdp admin
make argocd:apps       # déclare les apps staging + prod
```

Puis configurer le workflow `deploy.yml` pour le CI/CD automatique.

---

**Bonne chance ! 🚀**
