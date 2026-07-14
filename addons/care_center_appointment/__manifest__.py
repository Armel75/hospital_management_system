{
    'name': 'Centre Hospitalier - Rendez-vous',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Gestion des rendez-vous médicaux et planning',
    'description': """
        Gestion des Rendez-vous Médicaux
        =================================
        Ce module étend le socle hospitalier avec la gestion complète
        des rendez-vous médicaux et du planning.

        Fonctionnalités :
        - Planification des rendez-vous patients
        - Vue calendrier interactive (jour, semaine, mois)
        - Détection automatique des conflits d'agenda
        - Workflow complet : brouillon → confirmé → en cours → terminé
        - Génération automatique de la consultation au démarrage
        - Suivi des rendez-vous non honorés (noshow)
        - Agenda personnel par médecin
        - Statistiques et tableaux de bord
        - Numérotation automatique des rendez-vous
    """,
    'author': 'Top 1% Odoo Healthcare',
    'website': 'https://www.care-center.com',
    'depends': [
        'care_center_base',
        'care_center_consultation',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/appointment_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 3,
}
