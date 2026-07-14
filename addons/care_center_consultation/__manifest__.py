{
    'name': 'Centre Hospitalier - Consultations',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Gestion des consultations médicales',
    'description': """
        Gestion des Consultations Médicales
        =====================================
        Ce module étend le socle hospitalier avec la gestion complète
        des consultations médicales.

        Fonctionnalités :
        - Création et suivi des consultations (brouillon → en cours → terminé)
        - Saisie du motif, des symptômes et de l'anamnèse
        - Prise des constantes vitales (tension, pouls, température, SpO₂, IMC...)
        - Diagnostic et plan de traitement
        - Création automatique d'entrées dans le Dossier Médical Électronique
        - Numérotation automatique des consultations
        - Statistiques et tableaux de bord
    """,
    'author': 'Top 1% Odoo Healthcare',
    'website': 'https://www.care-center.com',
    'depends': [
        'care_center_base',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/consultation_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 2,
}
