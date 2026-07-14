# Contribuer au projet

Merci de votre intérêt pour le système de gestion hospitalière ! 🏥

## 🔧 Prérequis

- Docker & Docker Compose
- Python 3.10+
- Git
- pre-commit (optionnel mais recommandé)

## 🚀 Premiers pas

```bash
# Cloner le dépôt
git clone <url-du-depot>
cd hospital_management_system

# Configurer l'environnement
cp .env.example .env

# Démarrer les services
make up
```

## 📝 Conventions de code

### Python (Odoo)

- Conventions Odoo officielles : [Odoo Coding Guidelines](https://www.odoo.com/documentation/17.0/developer/reference/backend/coding_guidelines.html)
- Longueur de ligne maximale : 120 caractères
- Utiliser des noms de variables en anglais
- Docstrings en français (pour les utilisateurs finaux)
- Toujours déclarer `# -*- coding: utf-8 -*-` en tête de fichier
- Toujours hériter de `mail.thread` pour les modèles avec suivi

### XML (Vues Odoo)

- Indentation : 4 espaces
- Toujours entourer les vues de commentaires structurés
- Utiliser des `id` explicites suivant le pattern `view_{model}_{type}`

### Commits Git

```
type(contexte): description courte

- type : feat, fix, refactor, docs, style, test, chore
- contexte : module concerné (base, consultation, appointment...)
- description : en français, impératif présent
```

Exemples :
```
feat(consultation): ajout des constantes vitales
fix(pharmacy): correction du calcul du stock
docs(readme): mise à jour des instructions d'installation
```

## ✅ Avant de pusher

```bash
# Vérifier la qualité du code
make lint
make lint-xml

# Simuler la CI locale
make ci
```

## 🐛 Signaler un bug

Utilisez le template d'issue prévu à cet effet dans GitHub.

## 🧪 Tests

```bash
# Lancer les tests Odoo via Docker
docker compose run --rm odoo \
  odoo --test-enable --stop-after-init \
  -d test_hopital \
  -i care_center_base
```

## 📦 Structure des modules

```
addons/care_center_<module>/
├── __init__.py
├── __manifest__.py
├── data/
│   └── ...
├── models/
│   ├── __init__.py
│   └── *.py
├── security/
│   └── ir.model.access.csv
└── views/
    └── *.xml
```
