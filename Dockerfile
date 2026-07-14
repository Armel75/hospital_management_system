# =============================================================================
# Dockerfile — Image Odoo 17 personnalisée pour le Centre Hospitalier
# =============================================================================
# Utilisation :
#   En développement : docker compose up (utilise l'image officielle)
#   En CI/production : docker build -t care-center-odoo:latest .
#
# L'image officielle odoo:17 est utilisée comme base pour la reproduction
# exacte de l'environnement de développement.
# =============================================================================

FROM odoo:19

USER root

# Copier les modules personnalisés dans le répertoire addons
COPY ./addons /mnt/extra-addons

# Copier la configuration Odoo
COPY ./config/odoo.conf /etc/odoo/odoo.conf

# S'assurer que les permissions sont correctes
RUN chown -R odoo:odoo /mnt/extra-addons /etc/odoo/odoo.conf

USER odoo

EXPOSE 8069
