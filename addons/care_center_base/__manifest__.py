{
    'name': 'Centre Hospitalier - Base',
    'version': '1.0.0',
    'category': 'Healthcare',
    'summary': 'Module socle du système de gestion hospitalière',
    'description': """
        Gestion des patients et dossiers médicaux
        ==========================================
        Ce module est le socle du système de gestion hospitalière.
        Il gère :
        - Les fiches patients (identité, coordonnées, informations médicales)
        - Les dossiers médicaux électroniques (antécédents, allergies)
        - La numérotation automatique des patients
        - Le tableau de bord et les statistiques patients
    """,
    'author': 'Top 1% Odoo Healthcare',
    'website': 'https://www.care-center.com',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/hospital_groups.xml',
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'views/patient_views.xml',
        'views/medical_record_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 1,
}
