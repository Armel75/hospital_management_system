# 🏥 Centre Hospitalier — Système de Gestion Hospitalière (Odoo 17)

Suite de modules Odoo 17 pour la gestion complète d'un établissement de santé.

---

## 📦 Modules

| # | Module | Description | Statut |
|---|--------|-------------|--------|
| 1 | `care_center_base` | Socle : patients, dossiers médicaux, sécurité | ✅ |
| 2 | `care_center_consultation` | Consultations médicales, constantes vitales | ✅ |
| 3 | `care_center_appointment` | Rendez-vous, planning, vue calendrier | ✅ |
| 4 | `care_center_pharmacy` | Pharmacie : catalogue, lots, stocks, délivrances | ✅ |
| 5 | `care_center_billing` | Facturation, assurances, paiements | ✅ |

---

## 🚀 Démarrage rapide

### Prérequis

- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git
- make (optionnel, les commandes Docker fonctionnent directement)

### 1. Cloner le projet

```bash
git clone <url-du-depot>
cd hospital_management_system
```

### 2. Configuration de l'environnement

```bash
# Créer le fichier d'environnement
cp .env.example .env

# Modifier les mots de passe si nécessaire
# Éditer .env avec vos valeurs
```

### 3. Lancer les services

```bash
# Avec make
make up

# Ou directement avec Docker
docker compose up -d
```

### 4. Accéder à Odoo

| Service | URL |
|---------|-----|
| **Odoo** | [http://localhost:8069](http://localhost:8069) |
| **PostgreSQL** | `localhost:5432` (utilisateur : `odoo`) |

### 5. Installer les modules

1. Activer le **mode développeur** dans Odoo (Paramètres → Activer le mode développeur)
2. Aller dans **Applications → Mettre à jour la liste des applications**
3. Chercher et installer les modules dans l'ordre :
   - `care_center_base`
   - `care_center_consultation`
   - `care_center_appointment`
   - `care_center_pharmacy`
   - `care_center_billing`

---

## ⚙️ Commandes courantes

```bash
make up           # Démarrer les services
make down         # Arrêter les services
make logs         # Voir les logs en direct
make restart      # Redémarrer Odoo
make shell        # Shell bash dans le conteneur Odoo
```

### Sauvegarde et restauration

```bash
make backup                          # Sauvegarde complète (DB + fichiers)
make restore FILE=backup_20250714.dump  # Restauration
```

Ou via les scripts :

```bash
./scripts/backup.sh
./scripts/restore.sh ./backups/db_20250714.dump
```

---

## 🐳 Architecture Docker

```
┌──────────────┐    ┌──────────────┐
│   Odoo 17    │ ◄──►  PostgreSQL  │
│  port 8069   │    │   port 5432  │
└──────┬───────┘    └──────────────┘
       │
       ├── /mnt/extra-addons/   ← Modules personnalisés
       ├── /etc/odoo/odoo.conf  ← Configuration
       └── /var/lib/odoo/       ← Filestore (pièces jointes)
```

---

## 🗂️ Structure du projet

```
hospital_management_system/
├── addons/
│   ├── care_center_base/           ← Module socle
│   ├── care_center_consultation/   ← Consultations
│   ├── care_center_appointment/    ← Rendez-vous
│   ├── care_center_pharmacy/       ← Pharmacie
│   └── care_center_billing/        ← Facturation
├── config/
│   └── odoo.conf                   ← Configuration Odoo
├── scripts/
│   ├── backup.sh                   ← Sauvegarde DB + filestore
│   └── restore.sh                  ← Restauration DB
├── .env.example                    ← Modèle de configuration
├── .gitignore
├── docker-compose.yml              ← Services Docker
├── Dockerfile                      ← Image personnalisée (CI/prod)
├── Makefile                        ← Raccourcis de commandes
└── README.md                       ← Ce fichier
```

---

## 🔐 Sécurité

1. **Ne jamais commiter le fichier `.env`** (il est dans `.gitignore`)
2. Utiliser `.env.example` comme modèle pour les nouveaux développeurs
3. Changer les mots de passe par défaut en production
4. Le fichier de configuration `odoo.conf` contient le mot de passe admin hashé

---

## 🛠️ Développement

Les modules sont chargés dynamiquement via le volume Docker `./addons:/mnt/extra-addons`.
Toute modification dans `./addons/` est immédiatement visible dans Odoo après un redémarrage :

```bash
make restart
```

Pour installer un nouveau module : Mode développeur → Applications → Mettre à jour la liste → Installer.
