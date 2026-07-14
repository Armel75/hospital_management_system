# Changelog

Toutes les modifications notables de ce projet sont documentées ici.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] — 2025-07-14

### Ajouté

#### Modules Odoo
- **care_center_base** — Patients, dossiers médicaux électroniques, groupes de sécurité
- **care_center_consultation** — Consultations médicales, constantes vitales, DME automatique
- **care_center_appointment** — Rendez-vous, planning, vue calendrier, détection conflits
- **care_center_pharmacy** — Catalogue médicaments, lots/péremptions, mouvements stock, délivrances
- **care_center_billing** — Facturation, assurances, grille tarifaire, paiements

#### Infrastructure DevOps
- Docker Compose pour le développement (`docker-compose.yml`)
- Dockerfile pour l'image personnalisée Odoo 17
- Makefile avec commandes rapides (up, down, logs, backup, restore)
- Scripts de backup/restore PostgreSQL + filestore
- Configuration d'environnement via `.env.example`
- CI/CD GitHub Actions (lint, build, test)
- Pre-commit hooks (flake8, XML, whitespace)
- Documentation README complète
