# =============================================================================
# Makefile — Centre Hospitalier
# =============================================================================
# Commandes rapides pour le développement quotidien.
#
# Prérequis :
#   - Docker & Docker Compose
#   - make
#
# Utilisation :
#   make up        # Démarrer les services
#   make down      # Arrêter les services
#   make logs      # Voir les logs en direct
#   make restart   # Redémarrer Odoo uniquement
# =============================================================================

.DEFAULT_GOAL := help

# Couleurs pour l'affichage
BLUE := \033[1;36m
GREEN := \033[1;32m
YELLOW := \033[1;33m
RESET := \033[0m

.PHONY: help up down restart logs ps shell backup restore init

help: ## Affiche cette aide
	@echo "$(BLUE)╔══════════════════════════════════════════╗"
	@echo "║   Centre Hospitalier — Makefile            ║"
	@echo "╚══════════════════════════════════════════╝$(RESET)"
	@echo ""
	@echo "$(YELLOW)Commandes disponibles :$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)  %-15s$(RESET) %s\n", $$1, $$2}'

up: ## Démarre tous les services (Odoo + PostgreSQL)
	docker compose up -d
	@echo "$(GREEN)✅ Services démarrés :$(RESET)"
	@echo "   Odoo  → http://localhost:8069"
	@echo "   PostgreSQL → localhost:5432"

down: ## Arrête tous les services
	docker compose down
	@echo "$(GREEN)✅ Services arrêtés.$(RESET)"

restart: ## Redémarre uniquement le service Odoo
	docker compose restart odoo
	@echo "$(GREEN)✅ Odoo redémarré.$(RESET)"

logs: ## Affiche les logs en direct de tous les services
	docker compose logs -f

logs-odoo: ## Affiche les logs d'Odoo uniquement
	docker compose logs -f odoo

logs-db: ## Affiche les logs de PostgreSQL uniquement
	docker compose logs -f db

ps: ## Liste les services en cours
	docker compose ps

shell: ## Ouvre un shell bash dans le conteneur Odoo
	docker compose exec odoo bash

shell-db: ## Ouvre un shell PostgreSQL
	docker compose exec db psql -U odoo -d postgres

install: ## (Re)construit et démarre les services
	docker compose build --no-cache
	docker compose up -d
	@echo "$(GREEN)✅ Image reconstruite et services démarrés.$(RESET)"

backup: ## Sauvegarde la base de données et les fichiers
	@echo "$(YELLOW)⏳ Sauvegarde en cours...$(RESET)"
	@mkdir -p ./backups
	@docker compose exec db pg_dump -U odoo -d postgres -F c \
		-f /tmp/backup_$$(date +%Y%m%d_%H%M%S).dump
	@docker compose cp db:/tmp/backup_*.dump ./backups/
	@echo "$(GREEN)✅ Sauvegarde terminée : ./backups/$(RESET)"
	@ls -lh ./backups/*.dump 2>/dev/null | tail -1

restore: ## Restaure la base depuis le dernier backup (usage: make restore FILE=backup.dump)
	@if [ -z "$(FILE)" ]; then \
		echo "$(YELLOW)Usage: make restore FILE=nom_du_fichier.dump$(RESET)"; \
		echo "$(YELLOW)Fichiers disponibles :$(RESET)"; \
		ls -1 ./backups/*.dump 2>/dev/null || echo "   Aucun backup trouvé"; \
		exit 1; \
	fi
	@echo "$(YELLOW)⏳ Restauration de $(FILE)...$(RESET)"
	@docker compose cp ./backups/$(FILE) db:/tmp/restore.dump
	@docker compose exec db pg_restore -U odoo -d postgres --clean \
		/tmp/restore.dump
	@docker compose restart odoo
	@echo "$(GREEN)✅ Base restaurée depuis $(FILE).$(RESET)"

up-prod: ## Démarre en mode production (build depuis Dockerfile)
	docker compose -f docker-compose.prod.yml up -d --build
	@echo "$(GREEN)✅ Production démarrée : http://localhost:8069$(RESET)"

down-prod: ## Arrête la production
	docker compose -f docker-compose.prod.yml down
	@echo "$(GREEN)✅ Production arrêtée.$(RESET)"

lint: ## Vérifie la qualité du code Python (flake8)
	@echo "$(YELLOW)⏳ Vérification du code Python...$(RESET)"
	@pip install flake8 -q 2>/dev/null || true
	flake8 addons/ --max-line-length=120 --ignore=F841,E501,W503 --show-source --statistics
	@echo "$(GREEN)✅ Aucune erreur de lint.$(RESET)"

lint-xml: ## Vérifie la syntaxe XML
	@echo "$(YELLOW)⏳ Vérification des fichiers XML...$(RESET)"
	@for xml_file in $$(find addons/ -name "*.xml"); do \
		python -c "import xml.etree.ElementTree as ET; ET.parse('$$xml_file')" 2>/dev/null || \
		(echo "❌ Erreur XML dans : $$xml_file" && exit 1); \
	done; \
	echo "$(GREEN)✅ Tous les XML sont valides.$(RESET)"

precommit: ## Exécute les hooks pre-commit sur tous les fichiers
	@if command -v pre-commit &> /dev/null; then \
		pre-commit run --all-files; \
	else \
		echo "$(YELLOW)⚠️  pre-commit n'est pas installé.$(RESET)"; \
		echo "  pip install pre-commit"; \
		echo "  pre-commit install"; \
	fi

precommit-install: ## Installe les hooks pre-commit dans git
	pip install pre-commit
	pre-commit install
	@echo "$(GREEN)✅ Pre-commit installé.$(RESET)"

ci: ## Simule la CI localement (lint + build)
	@make lint
	@make lint-xml
	docker compose build
	@echo "$(GREEN)✅ CI locale passée.$(RESET)"

init: ## Initialisation du projet (copie .env, démarrage)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✅ Fichier .env créé depuis .env.example$(RESET)"; \
	else \
		echo "$(YELLOW)⚠️  Le fichier .env existe déjà, aucune modification.$(RESET)"; \
	fi
	@make up
